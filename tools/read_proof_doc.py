#!/usr/bin/env python3
"""Read the marked-up proofreading .docx back and report the corrections.

The proofing document (tools/make_proof_doc.js) prints one table row per
question: 題號 | 中文 | 拼音 | 英文語境與說明 | ✎ 修正. This reads the last
column, pairs it with the id in the first, and reports what changed — so the
corrections can be applied to the banks precisely rather than by eye.

    python3 tools/read_proof_doc.py ~/Desktop/中文題庫校對稿.docx
    python3 tools/read_proof_doc.py ~/Desktop/中文題庫校對稿.docx --json out.json

Also picks up Word tracked changes and comments, in case those were used
instead of (or as well as) the 修正 column.
"""
import argparse, json, pathlib, re, sys, zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ID_RE = re.compile(r"^[BIA]\d{3}$")


def cell_text(tc):
    """All visible text in a table cell, one line per paragraph.

    Includes <w:ins> (inserted) runs and skips <w:del> (deleted) ones, so a
    document marked up with tracked changes reads as the corrected version.
    """
    lines = []
    for para in tc.iter(f"{W}p"):
        buf = []
        for node in para.iter():
            if node.tag == f"{W}t":
                buf.append(node.text or "")
            elif node.tag == f"{W}br":
                buf.append("\n")
        text = "".join(buf).strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def read_rows(docx):
    with zipfile.ZipFile(docx) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    rows = []
    for tr in root.iter(f"{W}tr"):
        cells = [cell_text(tc) for tc in tr.findall(f"{W}tc")]
        if len(cells) < 5:
            continue
        qid = cells[0].split("\n")[0].strip()
        if not ID_RE.match(qid):
            continue                                   # header row
        rows.append({
            "id": qid,
            "zh": cells[1].strip(),
            "py": cells[2].strip(),
            "note": cells[4].strip(),
        })
    return rows


def read_comments(docx):
    """Word comments, keyed by nothing in particular — reported for eyeballing."""
    out = []
    with zipfile.ZipFile(docx) as z:
        if "word/comments.xml" not in z.namelist():
            return out
        root = ET.fromstring(z.read("word/comments.xml"))
        for c in root.iter(f"{W}comment"):
            txt = " ".join(t.text or "" for t in c.iter(f"{W}t")).strip()
            if txt:
                out.append({"author": c.get(f"{W}author", ""), "text": txt})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--data", default="fets/mandarin-challenge/data")
    ap.add_argument("--json", help="write the corrections to this file")
    args = ap.parse_args()

    path = pathlib.Path(args.docx).expanduser()
    if not path.exists():
        sys.exit(f"No such file: {path}")

    rows = read_rows(path)
    if not rows:
        sys.exit("No question rows found — is this the proofreading document?")

    # Cross-check against the live banks: every id must exist, and flag any
    # 中文/拼音 cell that was edited in place rather than noted in 修正.
    banks = {}
    for name in ("beginner", "intermediate", "advanced"):
        for q in json.loads((pathlib.Path(args.data) / f"{name}.json")
                            .read_text(encoding="utf-8"))["questions"]:
            banks[q["id"]] = q

    unknown = [r["id"] for r in rows if r["id"] not in banks]
    notes = [r for r in rows if r["note"]]
    inline = [r for r in rows
              if r["id"] in banks and not r["note"]
              and (r["zh"] != banks[r["id"]]["zh"] or r["py"] != banks[r["id"]]["py"])]

    print(f"{len(rows)} question rows read from {path.name}")
    print(f"  {len(banks)} questions in the banks"
          + (f" · {len(unknown)} UNKNOWN ids in the doc" if unknown else ""))
    if unknown:
        print("  unknown:", unknown[:10])

    if inline:
        print(f"\n{len(inline)} rows edited directly in the 中文/拼音 columns "
              f"(no note in 修正) — these count too:")
        for r in inline[:20]:
            b = banks[r["id"]]
            if r["zh"] != b["zh"]:
                print(f"  {r['id']} 中文  {b['zh']}  →  {r['zh']}")
            if r["py"] != b["py"]:
                print(f"  {r['id']} 拼音  {b['py']}  →  {r['py']}")

    print(f"\n{len(notes)} questions have corrections in the 修正 column:")
    for r in notes:
        print(f"\n  {r['id']}  {banks.get(r['id'], {}).get('zh', '?')}")
        for line in r["note"].split("\n"):
            print(f"      {line}")

    comments = read_comments(path)
    if comments:
        print(f"\n{len(comments)} Word comments:")
        for c in comments[:30]:
            print(f"  [{c['author']}] {c['text']}")

    if args.json:
        payload = {"corrections": notes, "inline_edits": inline, "comments": comments}
        pathlib.Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")

    if not notes and not inline and not comments:
        print("\nNothing marked up yet.")


main()
