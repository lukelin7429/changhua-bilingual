"""
Parse YouTube playlist descriptions for Word of the Day videos.
Reconcile against the existing wotd.csv:
  - Extract school + 4 sentences from each description
  - List videos where school could not be detected (for Luke to fill in)
  - Group duplicates by (keyword, sentence_1_en) — apply Luke's rule
  - List videos that exist in the playlist but not in wotd.csv (new videos)

Outputs (in changhua-bilingual/data/):
  - wotd_playlist_extracted.csv        full parsed catalog (3,029 rows)
  - wotd_missing_school.csv            videos where school couldn't be resolved
  - wotd_dedup_decisions.csv           per-group keep/drop with reason
  - wotd_new_videos.csv                in playlist but not in current wotd.csv
"""
import csv
import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

DESC_JSON = DATA / "wotd_playlist_descriptions.json"
SCHOOLS_YML = DATA / "schools.yml"
TOWNSHIPS_YML = DATA / "townships.yml"
EXISTING_CSV = DATA / "wotd.csv"

OUT_EXTRACTED = DATA / "wotd_playlist_extracted.csv"
OUT_MISSING_SCHOOL = DATA / "wotd_missing_school.csv"
OUT_DEDUP = DATA / "wotd_dedup_decisions.csv"
OUT_NEW = DATA / "wotd_new_videos.csv"
OUT_SUMMARY = DATA / "wotd_playlist_reconcile_summary.md"
OUT_NEW_WOTD_CSV = DATA / "wotd_rebuilt.csv"

CN_CHAR_RE = re.compile(r"[一-鿿]")
URL_RE = re.compile(r"https?://\S+")
SCHOOL_HEAD_RE = re.compile(
    r"彰化?[縣市線]?[一-鿿\s]*?(?:國[小中]|高中|高工|國中小)(?:[一-鿿]*分校)?"
)
OUT_OF_COUNTY_RE = re.compile(
    r"(?:台中|臺中|南投|雲林|台北|臺北|新北|高雄|台南|臺南|嘉義|苗栗|新竹|桃園|宜蘭|基隆|花蓮|台東|臺東|屏東|金門|連江)市?[一-鿿]+國[小中]"
)
KEYWORD_REPEAT_RE = re.compile(r"^[A-Za-z][A-Za-z\s\(\)\-/]*\s*(\([nvad][a-z]*\.?\))?\s*[一-鿿]*\s*$")


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_school_index(schools_data, townships_data):
    """Return (canonical_full_name → slug, helpful lookup tables)."""
    townships_by_zh = {t["zh"]: t for t in townships_data["townships"]}
    townships_by_slug = {t["slug"]: t for t in townships_data["townships"]}

    schools = schools_data["schools"]
    # Canonical full name = 彰化縣 + township_zh + school.zh
    full_to_slug = {}
    short_to_slugs = defaultdict(list)
    slug_to_meta = {}

    for s in schools:
        tw = townships_by_slug[s["township"]]
        full = "彰化縣" + tw["zh"] + s["zh"]
        full_to_slug[full] = s["slug"]
        short_to_slugs[s["zh"]].append(s["slug"])
        slug_to_meta[s["slug"]] = {
            "slug": s["slug"],
            "name": s["name"],
            "zh": s["zh"],
            "township_slug": tw["slug"],
            "township_zh": tw["zh"],
            "full_zh": full,
        }
    return full_to_slug, short_to_slugs, slug_to_meta, townships_by_zh


def parse_title(title):
    """Return (keyword, keyword_zh) from 'Word of the Day: <keyword> <keyword_zh>'."""
    body = re.sub(r"^Word\s*of\s*the\s*Day\s*[:：]\s*", "", title.strip(), flags=re.I)
    # Find first Chinese character
    m = CN_CHAR_RE.search(body)
    if m:
        keyword = body[: m.start()].strip()
        keyword_zh = body[m.start():].strip()
    else:
        keyword = body.strip()
        keyword_zh = ""
    return keyword, keyword_zh


TOWNSHIP_ALIASES = {
    # description sometimes uses old township names or typos — map to canonical zh
    "員林鎮": "員林市",
    "員林": "員林市",     # missing 市
    "新港鄉": "伸港鄉",   # frequent typo
    "港鄉": "伸港鄉",     # truncated
    "伸港": "伸港鄉",     # missing 鄉
    "伸港新": "伸港鄉",   # description typo: 伸港新大同國小 → 伸港鄉大同國小
    "芳園鄉": "芬園鄉",   # typo
    "福鄉鄉": "福興鄉",   # typo
    "員社頭鄉": "社頭鄉",
    "社頭心": "社頭鄉",
    "社頭": "社頭鄉",    # missing 鄉
}


def normalize_school_short(candidate, townships_by_zh):
    """Reduce `彰化縣XX鄉YY國小` (any prefix variant) down to `YY國小`."""
    # Collapse internal whitespace
    s = re.sub(r"\s+", "", candidate)
    # Strip suffixes
    s = re.sub(r"雙語(?:資源)?網[站]?$", "", s)
    # Normalize 線 ↔ 縣 typo at prefix
    s = re.sub(r"^彰化線", "彰化縣", s)
    # Strip 彰化縣 / 彰化市 / 彰化 prefix in order of specificity
    if s.startswith("彰化縣彰化市"):
        s = s[len("彰化縣彰化市"):]
    elif s.startswith("彰化縣"):
        s = s[len("彰化縣"):]
    elif s.startswith("彰化市"):
        s = s[len("彰化市"):]
    elif s.startswith("彰化"):
        s = s[len("彰化"):]
    # Strip 縣立/市立 prefix (e.g., 彰化縣立信義國中 → 立信義國中 → 信義國中)
    s = re.sub(r"^(縣立|市立|立)", "", s)
    # Strip any leading township zh (longest match wins; also alias map)
    township_names = sorted(list(townships_by_zh.keys()) + list(TOWNSHIP_ALIASES.keys()), key=len, reverse=True)
    for tw in township_names:
        if s.startswith(tw):
            s = s[len(tw):]
            break
    # Strip 縣立/立 again in case it was after township
    s = re.sub(r"^(縣立|市立|立)", "", s)
    return s


def detect_school(desc, full_to_slug, short_to_slugs, slug_to_meta, townships_by_zh, all_school_zh):
    """Return (slug, full_zh, raw_match, status).
    status ∈ {ok, out_of_county, mcc_self, ccc_ny, school_not_in_yml, missing}.
    """
    lines = [ln.strip() for ln in desc.splitlines() if ln.strip()]
    # Check non-school contributors first (line 1 only, by exact substring)
    if lines:
        head_block = " ".join(lines[:2])
        if "人師教育協會" in head_block or "人師協會" in head_block:
            return None, None, "彰化縣人師教育協會", "mcc_self"
        if "紐約首府華社中文學校" in head_block or "CCC " in head_block or head_block.startswith("CCC"):
            return None, None, "CCC 紐約首府華社中文學校", "ccc_ny"

    raw = None
    for ln in lines[:5]:  # search first 5 lines, not just 3
        m = SCHOOL_HEAD_RE.search(ln)
        if m:
            raw = re.sub(r"\s+", "", m.group(0))
            break
    if not raw:
        # Try: vocational schools (高級工業職業學校 etc.)
        VOCATIONAL_RE = re.compile(r"彰化[縣市]?[一-鿿]*?(?:高級工業職業學校|高級商業職業學校|職業學校|工業職業學校)")
        for ln in lines[:5]:
            m = VOCATIONAL_RE.search(ln)
            if m:
                raw = re.sub(r"\s+", "", m.group(0))
                # Map full vocational name → 高工/高商
                raw_short = re.sub(r"高級工業職業學校$", "高工", raw)
                raw_short = re.sub(r"高級商業職業學校$", "高商", raw_short)
                if raw_short != raw:
                    raw = raw_short
                break
    if not raw:
        # No-prefix school name (e.g., "湳雅國小", "中山國小")
        NOPREFIX_RE = re.compile(r"^([一-鿿]{2,5}(?:國[小中]|高中|高工))")
        for ln in lines[:3]:
            m = NOPREFIX_RE.match(ln)
            if m:
                short = m.group(1)
                if short in short_to_slugs and len(short_to_slugs[short]) == 1:
                    slug = short_to_slugs[short][0]
                    return slug, slug_to_meta[slug]["full_zh"], short, "ok"
    if not raw:
        for ln in lines[:5]:
            m = OUT_OF_COUNTY_RE.search(ln)
            if m:
                return None, None, re.sub(r"\s+", "", m.group(0)), "out_of_county"
        return None, None, None, "missing"

    # Try direct full match
    candidate = re.sub(r"雙語(?:資源)?網[站]?$", "", raw)
    if candidate in full_to_slug:
        return full_to_slug[candidate], candidate, raw, "ok"

    short = normalize_school_short(candidate, townships_by_zh)

    def try_lookup(s):
        slugs = short_to_slugs.get(s, [])
        if len(slugs) == 1:
            return slugs[0]
        return None

    slug = try_lookup(short)
    if slug:
        return slug, slug_to_meta[slug]["full_zh"], raw, "ok"

    # Variants
    variants = set()
    variants.add(short)
    # 國中 ↔ 國中小 (suffix variants)
    if short.endswith("國中") and not short.endswith("國中小"):
        variants.add(short + "小")
    if short.endswith("國中小"):
        variants.add(short[:-1])
    # Strip 分校 entirely (since schools.yml treats 成功國小 = main+branch as one entry)
    # Match 國[小中] followed by any chars then 分校 at end, replace with just 國[小中]
    if "分校" in short:
        no_branch = re.sub(r"國([小中])[一-鿿]*?分校$", r"國\1", short)
        if no_branch and no_branch != short:
            variants.add(no_branch)
    # Char variants
    char_map = {"豊": "豐", "豐": "豊", "禮": "礼", "礼": "禮", "得": "德", "州": "洲", "洲": "州"}
    for c1, c2 in char_map.items():
        if c1 in short:
            variants.add(short.replace(c1, c2))
    # Strip extra 裡 char
    if "裡" in short:
        variants.add(short.replace("裡", ""))

    for v in variants:
        if not v:
            continue
        slug = try_lookup(v)
        if slug:
            return slug, slug_to_meta[slug]["full_zh"], raw, "ok"

    # A 彰化 school was detected but doesn't match schools.yml — likely a real
    # school that needs to be added to schools.yml (e.g., 王功國小, 鹿東國小).
    return None, None, raw, "school_not_in_yml"


def detect_truncated_school(desc, full_to_slug, short_to_slugs, slug_to_meta, townships_by_zh):
    """Last-ditch attempt: '彰化縣XX鄉YY' (no 國小 suffix) → infer YY國小."""
    lines = [ln.strip() for ln in desc.splitlines() if ln.strip()]
    # Match "彰化縣XX鄉YY" at end of line OR followed by | (school name truncated, no 國小 suffix)
    PAT = re.compile(r"彰化縣([一-鿿]{2,4})([一-鿿]{2,4})(?:\s*[|│｜]|$)")
    for ln in lines[:3]:
        m = PAT.search(ln)
        if not m:
            continue
        town_part, school_part = m.group(1), m.group(2)
        if town_part not in townships_by_zh:
            continue
        for suffix in ("國小", "國中"):
            short = school_part + suffix
            slugs = short_to_slugs.get(short, [])
            if len(slugs) == 1:
                slug = slugs[0]
                if slug_to_meta[slug]["township_zh"] == town_part:
                    return slug, slug_to_meta[slug]["full_zh"], "彰化縣" + town_part + short, "ok"
    return None, None, None, None


def parse_sentences(desc, school_raw):
    """Return (s1_en, s1_zh, s2_en, s2_zh)."""
    lines = [ln.strip() for ln in desc.splitlines() if ln.strip()]
    if school_raw:
        # Remove the line containing the school match (only the first occurrence)
        removed = False
        new_lines = []
        for ln in lines:
            if not removed and school_raw in ln:
                # If the line is exactly school_raw (or school+URL), drop it.
                # If it has substantial extra text (a sentence), keep without the school.
                stripped = ln.replace(school_raw, "").strip()
                stripped = URL_RE.sub("", stripped).strip()
                stripped = re.sub(r"雙語(?:資源)?網[站]?", "", stripped).strip()
                if not stripped or len(stripped) < 5:
                    removed = True
                    continue
                new_lines.append(stripped)
                removed = True
            else:
                new_lines.append(ln)
        lines = new_lines

    # Drop pure URL lines
    lines = [ln for ln in lines if not URL_RE.fullmatch(ln.strip())]
    lines = [URL_RE.sub("", ln).strip() for ln in lines]
    lines = [ln for ln in lines if ln]

    # Drop keyword-repeat lines: short, only English/POS marker + optional Chinese gloss
    def is_keyword_line(ln):
        if len(ln) > 25:
            return False
        return bool(KEYWORD_REPEAT_RE.match(ln))

    # Only strip leading keyword-repeat lines (max 1)
    if lines and is_keyword_line(lines[0]):
        lines = lines[1:]

    s1_en = s1_zh = s2_en = s2_zh = ""

    # Pattern: 4 lines = EN, ZH, EN, ZH
    def split_en_zh(line):
        """If a line contains both EN and ZH, split into (en, zh)."""
        m = CN_CHAR_RE.search(line)
        if not m:
            return line.strip(), ""
        en = line[: m.start()].strip()
        zh = line[m.start():].strip()
        return en, zh

    # Normalize: split mixed lines first
    pairs = []
    en_only = []
    zh_only = []
    for ln in lines:
        en, zh = split_en_zh(ln)
        if en and zh:
            pairs.append((en, zh))
        elif en:
            en_only.append(en)
        elif zh:
            zh_only.append(zh)

    if pairs and not en_only and not zh_only:
        # Each line was self-contained EN+ZH
        if len(pairs) >= 1:
            s1_en, s1_zh = pairs[0]
        if len(pairs) >= 2:
            s2_en, s2_zh = pairs[1]
    elif en_only and zh_only:
        # Alternating EN / ZH lines
        if len(en_only) >= 1:
            s1_en = en_only[0]
        if len(zh_only) >= 1:
            s1_zh = zh_only[0]
        if len(en_only) >= 2:
            s2_en = en_only[1]
        if len(zh_only) >= 2:
            s2_zh = zh_only[1]
        # If there were ALSO mixed lines, append them where missing
        for en, zh in pairs:
            if not s2_en:
                s2_en, s2_zh = en, zh
                break
    elif pairs and (en_only or zh_only):
        if pairs:
            s1_en, s1_zh = pairs[0]
        if len(pairs) >= 2:
            s2_en, s2_zh = pairs[1]
        elif en_only and zh_only:
            s2_en, s2_zh = en_only[0], zh_only[0]

    return s1_en, s1_zh, s2_en, s2_zh


def youtube_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def main():
    schools_data = load_yaml(SCHOOLS_YML)
    townships_data = load_yaml(TOWNSHIPS_YML)
    full_to_slug, short_to_slugs, slug_to_meta, townships_by_zh = build_school_index(
        schools_data, townships_data
    )

    with DESC_JSON.open(encoding="utf-8") as f:
        items = json.load(f)

    # Load existing wotd.csv
    existing_ids = set()
    existing_keyword_school_pairs = set()
    with EXISTING_CSV.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            url = row.get("youtube", "")
            m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", url)
            if m:
                existing_ids.add(m.group(1))
            existing_keyword_school_pairs.add((row.get("keyword", ""), row.get("school", "")))

    all_school_zh = list({s["zh"] for s in schools_data["schools"]})

    # Resolve once; cache per item index
    resolutions = []
    for item in items:
        res = detect_school(item["desc"], full_to_slug, short_to_slugs, slug_to_meta, townships_by_zh, all_school_zh)
        # Fallback: truncated 國小 suffix (e.g., "彰化縣田中鎮明禮 | ...")
        if res[3] == "missing":
            alt = detect_truncated_school(item["desc"], full_to_slug, short_to_slugs, slug_to_meta, townships_by_zh)
            if alt[0]:
                res = alt
        resolutions.append(res)

    # Counters (only count resolved schools)
    school_total_counts = Counter()
    township_total_counts = Counter()
    for slug, _, _, status in resolutions:
        if slug:
            school_total_counts[slug] += 1
            township_total_counts[slug_to_meta[slug]["township_slug"]] += 1

    parsed_rows = []
    missing_school_rows = []
    resolution_status_counts = Counter()

    for item, (slug, full_zh, raw, status) in zip(items, resolutions):
        vid = item["id"]
        title = item["title"]
        desc = item["desc"]
        keyword, keyword_zh = parse_title(title)
        s1_en, s1_zh, s2_en, s2_zh = parse_sentences(desc, raw)
        resolution_status_counts[status] += 1

        row = {
            "video_id": vid,
            "title": title,
            "keyword": keyword,
            "keyword_zh": keyword_zh,
            "school_slug": slug or "",
            "school_zh": full_zh or "",
            "school_raw": raw or "",
            "school_status": status,
            "township_slug": slug_to_meta[slug]["township_slug"] if slug else "",
            "sentence_1": s1_en,
            "sentence_1_zh": s1_zh,
            "sentence_2": s2_en,
            "sentence_2_zh": s2_zh,
            "youtube": youtube_url(vid),
            "in_existing_csv": vid in existing_ids,
        }
        parsed_rows.append(row)

        if not slug:
            missing_school_rows.append({
                "video_id": vid,
                "youtube": youtube_url(vid),
                "title": title,
                "keyword": keyword,
                "keyword_zh": keyword_zh,
                "school_raw": raw or "(none in desc)",
                "status": status,
                "desc_preview": desc.replace("\n", " | ")[:140],
            })

    # Write extracted catalog
    extracted_fields = [
        "video_id", "title", "keyword", "keyword_zh",
        "school_slug", "school_zh", "school_raw", "school_status", "township_slug",
        "sentence_1", "sentence_1_zh", "sentence_2", "sentence_2_zh",
        "youtube", "in_existing_csv",
    ]
    with OUT_EXTRACTED.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=extracted_fields)
        w.writeheader()
        w.writerows(parsed_rows)

    # Write missing-school list
    with OUT_MISSING_SCHOOL.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["video_id", "youtube", "title", "keyword", "keyword_zh", "school_raw", "status", "desc_preview"])
        w.writeheader()
        w.writerows(missing_school_rows)

    # Dedup: group by (keyword, sentence_1)
    # Only consider rows that have a school and a non-empty sentence_1
    groups = defaultdict(list)
    for r in parsed_rows:
        if not r["school_slug"] or not r["sentence_1"]:
            continue
        key = (r["keyword"].strip().lower(), r["sentence_1"].strip().lower())
        groups[key].append(r)

    dedup_decisions = []
    for key, members in groups.items():
        if len(members) <= 1:
            continue  # not a duplicate group
        # Sort by Luke's rule (primary intent: maximize school name diversity):
        # 1) school with FEWEST videos in playlist (give airtime to underexposed schools)
        # 2) township with fewest videos (tiebreak — also prefer underrepresented townships)
        # 3) stable: video_id
        def sort_key(r):
            return (
                school_total_counts[r["school_slug"]],
                township_total_counts[r["township_slug"]],
                r["video_id"],
            )
        sorted_members = sorted(members, key=sort_key)
        keep = sorted_members[0]
        for i, m in enumerate(sorted_members):
            dedup_decisions.append({
                "group_keyword": key[0],
                "group_sentence_1": key[1][:120],
                "video_id": m["video_id"],
                "youtube": m["youtube"],
                "school_zh": m["school_zh"],
                "school_total_videos": school_total_counts[m["school_slug"]],
                "township_slug": m["township_slug"],
                "township_total_videos": township_total_counts[m["township_slug"]],
                "decision": "KEEP" if i == 0 else "DROP",
                "reason": f"kept: smallest school count ({school_total_counts[keep['school_slug']]} videos)" if i == 0
                         else f"dropped: same as {keep['video_id']} ({keep['school_zh']})",
            })

    with OUT_DEDUP.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "group_keyword", "group_sentence_1", "video_id", "youtube",
            "school_zh", "school_total_videos",
            "township_slug", "township_total_videos",
            "decision", "reason",
        ])
        w.writeheader()
        w.writerows(dedup_decisions)

    # Build school display string for each row (for the rebuilt wotd.csv).
    # Use canonical 彰化縣XX鄉YY國小 for resolved schools; contributor name for mcc/ccc;
    # raw match for out-of-county / school_not_in_yml; empty for missing.
    def school_display(r):
        status = r["school_status"]
        if status == "ok":
            return r["school_zh"]
        if status == "mcc_self":
            return "彰化縣人師教育協會"
        if status == "ccc_ny":
            return "紐約中文學校"
        if status in ("out_of_county", "school_not_in_yml"):
            return r["school_raw"]
        return ""  # missing

    # Drop set from dedup decisions
    drop_ids = {d["video_id"] for d in dedup_decisions if d["decision"] == "DROP"}

    # Rebuild wotd.csv: all playlist rows minus dedup drops
    rebuilt_rows = []
    for r in parsed_rows:
        if r["video_id"] in drop_ids:
            continue
        rebuilt_rows.append({
            "keyword": r["keyword"],
            "keyword_zh": r["keyword_zh"],
            "sentence_1": r["sentence_1"],
            "sentence_1_zh": r["sentence_1_zh"],
            "sentence_2": r["sentence_2"],
            "sentence_2_zh": r["sentence_2_zh"],
            "school": school_display(r),
            "youtube": r["youtube"],
        })

    with OUT_NEW_WOTD_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["keyword", "keyword_zh", "sentence_1", "sentence_1_zh", "sentence_2", "sentence_2_zh", "school", "youtube"])
        w.writeheader()
        w.writerows(rebuilt_rows)

    # New videos: in playlist but NOT in existing wotd.csv
    new_rows = [r for r in parsed_rows if not r["in_existing_csv"]]
    new_fields = [
        "video_id", "title", "keyword", "keyword_zh",
        "school_slug", "school_zh", "township_slug",
        "sentence_1", "sentence_1_zh", "sentence_2", "sentence_2_zh",
        "youtube",
    ]
    with OUT_NEW.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=new_fields)
        w.writeheader()
        for r in new_rows:
            w.writerow({k: r.get(k, "") for k in new_fields})

    # Summary
    school_detected = sum(1 for r in parsed_rows if r["school_slug"])
    sentence_detected = sum(1 for r in parsed_rows if r["sentence_1"])
    dup_groups = sum(1 for g in groups.values() if len(g) > 1)
    dup_drops = sum(1 for d in dedup_decisions if d["decision"] == "DROP")

    # Top missing schools (raw → count) for the summary
    missing_raw_counts = Counter()
    not_in_yml_counts = Counter()
    for r in missing_school_rows:
        if r["status"] == "school_not_in_yml":
            not_in_yml_counts[r["school_raw"]] += 1
        elif r["status"] == "missing":
            missing_raw_counts[r["school_raw"] or "(no school in description)"] += 1

    summary = []
    summary.append("# WOTD Playlist 對齊 wotd.csv — 摘要報告\n")
    summary.append(f"產出日期：自動生成 / 來源 playlist：3,029 支 / 既有 wotd.csv：{len(existing_ids)} 唯一影片\n")
    summary.append("## 解析統計\n")
    summary.append("| 狀態 | 數量 | 說明 |")
    summary.append("|---|---:|---|")
    summary.append(f"| `ok` | {resolution_status_counts.get('ok', 0)} | 學校名對齊 schools.yml 成功 |")
    summary.append(f"| `mcc_self` | {resolution_status_counts.get('mcc_self', 0)} | 人師教育協會自製（非學校 contributor）|")
    summary.append(f"| `ccc_ny` | {resolution_status_counts.get('ccc_ny', 0)} | CCC 紐約首府華社中文學校（跨組織）|")
    summary.append(f"| `out_of_county` | {resolution_status_counts.get('out_of_county', 0)} | 非彰化縣學校（台中／南投等跨縣合作）|")
    summary.append(f"| `school_not_in_yml` | {resolution_status_counts.get('school_not_in_yml', 0)} | 彰化學校但 schools.yml 沒收錄 → **需補進 schools.yml** |")
    summary.append(f"| `missing` | {resolution_status_counts.get('missing', 0)} | 描述沒夠線索抓到學校 → **手動查補** |")
    summary.append("")
    summary.append(f"句子抽取：sentence_1 命中 {sentence_detected} / {len(parsed_rows)}\n")
    summary.append("## 新增影片\n")
    summary.append(f"- Playlist 上但 wotd.csv 沒收錄：**{len(new_rows)} 支**")
    summary.append(f"- 已收錄：{sum(1 for r in parsed_rows if r['in_existing_csv'])} 支")
    summary.append(f"- → 詳見 `{OUT_NEW.name}`\n")
    summary.append("## 去重決策\n")
    summary.append(f"- 重複群組（同 keyword + 同 sentence_1）：**{dup_groups} 組**")
    summary.append(f"- 規則：(1) 校影片數少的優先（讓更多學校露臉）(2) 鄉鎮代表性少的為 tiebreaker (3) video_id 穩定")
    summary.append(f"- 結果：{dup_drops} 支建議移除、{dup_groups} 支保留")
    summary.append(f"- → 詳見 `{OUT_DEDUP.name}`\n")
    summary.append("## 需要補進 schools.yml 的學校\n")
    summary.append("這些是 description 裡有「彰化XX國小/國中」但 schools.yml 找不到的：\n")
    summary.append("| 學校 | 影片數 |")
    summary.append("|---|---:|")
    for school, count in sorted(not_in_yml_counts.items(), key=lambda x: -x[1]):
        summary.append(f"| {school} | {count} |")
    summary.append("")
    summary.append("## 描述沒線索的影片（11 支需手動查）\n")
    summary.append(f"見 `{OUT_MISSING_SCHOOL.name}` 中 status=missing 的列。\n")
    OUT_SUMMARY.write_text("\n".join(summary), encoding="utf-8")

    print(f"Parsed {len(parsed_rows)} playlist videos.")
    print(f"  School resolution: {dict(resolution_status_counts)}")
    print(f"  School resolved:   {school_detected} / {len(parsed_rows)}  ({len(parsed_rows) - school_detected} non-ok → see {OUT_MISSING_SCHOOL.name})")
    print(f"  sentence_1 found:  {sentence_detected} / {len(parsed_rows)}")
    print(f"  Already in wotd.csv: {sum(1 for r in parsed_rows if r['in_existing_csv'])}")
    print(f"  Net new videos:    {len(new_rows)}  (see {OUT_NEW.name})")
    print(f"  Duplicate groups:  {dup_groups}  → {dup_drops} drops, {dup_groups} keeps  (see {OUT_DEDUP.name})")
    print(f"  Summary report:    {OUT_SUMMARY.name}")
    print(f"  Rebuilt wotd.csv:  {OUT_NEW_WOTD_CSV.name}  ({len(rebuilt_rows)} rows after dedup)")


if __name__ == "__main__":
    main()
