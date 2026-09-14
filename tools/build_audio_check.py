#!/usr/bin/env python3
"""Refresh the phrase list inside the audio proofing page.

fets/mandarin-challenge/audio-check/ carries its own copy of every phrase,
pinyin and clip hash so the page is a single file with no fetch. That copy goes
stale the moment a question's pinyin or phrase changes, and a proofing tool
showing the wrong pinyin is worse than no tool — so re-run this after editing
any bank:

    python3 tools/build_audio_check.py

Only the <script id="data"> block is rewritten; the page itself is hand-edited.
"""
import json, pathlib, re, sys

BANKS = ("beginner", "intermediate", "advanced")
DATA = pathlib.Path("fets/mandarin-challenge/data")
PAGE = pathlib.Path("fets/mandarin-challenge/audio-check/index.html")
MANIFEST = pathlib.Path("learn/audio-manifest.json")
ROUND_SIZE = 20
ROUNDS = 9


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out, missing = {}, []

    for level in BANKS:
        questions = json.loads((DATA / f"{level}.json").read_text(encoding="utf-8"))["questions"]
        for n in range(1, ROUNDS + 1):
            rows, seen = [], set()
            for q in questions[(n - 1) * ROUND_SIZE: n * ROUND_SIZE]:
                zh = q.get("zh")
                if not zh or zh in seen:
                    continue
                seen.add(zh)
                h = manifest.get(zh)
                if not h:
                    missing.append(f"{q['id']} {zh}")
                    continue
                rows.append({"zh": zh, "py": q.get("py", ""), "h": h, "id": q["id"]})
            out.setdefault(f"M{n}", {})[level] = rows

    if missing:
        print(f"warning: {len(missing)} phrases have no clip in the manifest "
              f"(e.g. {missing[:3]}) — run tools/gen_audio.py", file=sys.stderr)

    html = PAGE.read_text(encoding="utf-8")
    blob = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    new, count = re.subn(
        r'(<script id="data" type="application/json">).*?(</script>)',
        lambda m: m.group(1) + blob.replace("\\", "\\\\") + m.group(2),
        html, count=1, flags=re.S)
    if count != 1:
        sys.exit("could not find the <script id=\"data\"> block in the page")

    PAGE.write_text(new, encoding="utf-8")
    total = sum(len(v) for r in out.values() for v in r.values())
    print(f"{PAGE}: {total} clips across {len(out)} rounds")


main()
