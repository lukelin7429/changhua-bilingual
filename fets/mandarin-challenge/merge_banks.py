#!/usr/bin/env python3
"""Merge the new question batches into the three Mandarin Challenge banks,
even out the A/B/C/D answer distribution, and verify everything before writing.

Balancing rotates each question's four options so the correct answer lands on a
target letter. Rotation preserves every option's text — only the order changes —
so a question can never become wrong. Targets are assigned deterministically
(by hash of the question id) so re-running produces an identical file.
"""
import json, re, hashlib, pathlib, sys, collections
from stem_pinyin import STEM_PY

BASE = pathlib.Path("/Users/hayashikisshou/Library/Mobile Documents/com~apple~CloudDocs/"
                    "Documents/changhua-bilingual/fets/mandarin-challenge/data")
FRAG = pathlib.Path("/private/tmp/claude-501/-Users-hayashikisshou-Downloads/"
                    "2c619426-3c42-4783-a92e-b9bf96968a16/scratchpad")

LEVELS = {
    "beginner":     ["b1.json", "b2.json", "b3.json"],
    "intermediate": ["i1.json", "i2.json", "i3.json"],
    "advanced":     ["a1.json", "a2.json", "a3.json"],
}
TARGET = 180  # 9 meetings x 20

# Typos caught during authoring.
PATCHES = {
    "I111": {"zh": "麻煩你下午三點到辦公室", "py": "máfan nǐ xiàwǔ sān diǎn dào bàngōngshì"},
    "I164": {"why": "名單 (míngdān) = list of names. Common in Taiwanese offices: "
                    "參加名單 (participant list), 得獎名單 (winners' list)."},
    # Stem mentions both the short and full form; gloss the short one inline.
    "I135": {"q": "共備 (gòngbèi) is short for 共同備課, which means —"},
}

CJK = re.compile(r"[一-鿿][一-鿿，。？！、]*")
ALLOWED = re.compile(r"^[ -~ -ɏ -⁯←-⇿"
                     r"①-⓿─-➿　-〿一-鿿"
                     r"＀-￯\U0001F300-\U0001FAFF]*$")

def rotate(opts, ok, target):
    """Put the correct option at index `target` by cyclic rotation."""
    k = (ok - target) % 4
    return [opts[(i + k) % 4] for i in range(4)], target

def main():
    problems = []
    for level, frags in LEVELS.items():
        path = BASE / f"{level}.json"
        bank = json.loads(path.read_text(encoding="utf-8"))
        # Idempotent: a question already in the bank is replaced, not appended,
        # so re-running after a fix never doubles the file up.
        qs, seen = [], {}
        for q in list(bank["questions"]) + [x for f in frags
                                            for x in json.loads((FRAG / f).read_text(encoding="utf-8"))]:
            if q["id"] in seen:
                qs[seen[q["id"]]] = q
            else:
                seen[q["id"]] = len(qs)
                qs.append(q)

        for q in qs:
            if q["id"] in PATCHES:
                q.update(PATCHES[q["id"]])
            # Widen zh/py to the full phrase the stem actually shows, so no
            # Chinese ever appears on screen without a pinyin reading.
            if q["id"] in STEM_PY:
                q["zh"], q["py"] = STEM_PY[q["id"]]

        # ---- structural checks before touching anything ----
        ids = [q["id"] for q in qs]
        dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
        if dupes:
            problems.append(f"{level}: duplicate ids {dupes}")
        if len(qs) != TARGET:
            problems.append(f"{level}: {len(qs)} questions, expected {TARGET}")

        for q in qs:
            for k in ("id", "type", "zh", "py", "q", "why"):
                if not q.get(k):
                    problems.append(f"{q['id']}: missing {k}")
            if len(q.get("opts", [])) != 4:
                problems.append(f"{q['id']}: {len(q.get('opts', []))} options")
            if len(set(q["opts"])) != 4:
                problems.append(f"{q['id']}: duplicate option text")
            if not isinstance(q.get("ok"), int) or not 0 <= q["ok"] < 4:
                problems.append(f"{q['id']}: bad ok {q.get('ok')}")
            if "speak" in q:
                problems.append(f"{q['id']}: stale 'speak' field")
            # every Chinese run in the stem must carry pinyin somewhere
            for run in CJK.findall(q["q"]):
                run = run.strip("，。？！、")
                if run and run not in q["zh"] and f"{run} (" not in q["q"]:
                    problems.append(f"{q['id']}: stem {run!r} has no pinyin")
            # catch stray characters from other scripts
            for field in ("zh", "py", "q", "why", *q["opts"]):
                if not ALLOWED.match(field):
                    bad = [c for c in field if not ALLOWED.match(c)]
                    problems.append(f"{q['id']}: stray characters {bad!r}")

        if problems:
            continue  # don't rewrite a bank that failed its checks

        # ---- even out A/B/C/D ----
        order = sorted(range(len(qs)), key=lambda i: hashlib.md5(qs[i]["id"].encode()).hexdigest())
        pool = [0, 1, 2, 3] * (TARGET // 4)
        for rank, idx in enumerate(order):
            q = qs[idx]
            correct_text = q["opts"][q["ok"]]
            q["opts"], q["ok"] = rotate(q["opts"], q["ok"], pool[rank])
            assert q["opts"][q["ok"]] == correct_text, q["id"]  # rotation must preserve the answer

        bank["questions"] = qs
        bank["rounds"] = TARGET // 20
        path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        c = collections.Counter(q["ok"] for q in qs)
        t = collections.Counter(q["type"] for q in qs)
        print(f"{level:13s} {len(qs)} questions  ABCD={[c[i] for i in range(4)]}  {dict(t)}")

    if problems:
        print("\nFAILED — nothing written for the affected banks:")
        for p in problems[:40]:
            print(" -", p)
        print(f"({len(problems)} problems)")
        sys.exit(1)
    print("\nAll banks merged, balanced and verified. ✓")

main()
