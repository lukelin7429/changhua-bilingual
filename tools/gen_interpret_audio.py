"""Natural-voice English clips for the Interpreting Lab (/interpret/).

The app's questions live in interpret/data/m*.json, not in data-say
attributes, so gen_en_audio.py's page scanner can't see them. This wraps the
same pipeline (same voice, rate, hashing, R2 layout) and only swaps in a
collector that reads the JSON banks.

Voiced: English prompts, the correct English answer, "也可以這樣說" alternates,
vocabulary terms and their example sentences. Wrong options are never voiced.

    python3 tools/gen_interpret_audio.py
    ./tools/upload_en_audio.sh
    git add audio/manifest/interpret.json
"""
import asyncio, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gen_en_audio as g  # noqa: E402

DATA = g.ROOT / "interpret" / "data"


def texts():
    out = set()
    for f in sorted(DATA.glob("m*.json")):
        bank = json.loads(f.read_text(encoding="utf-8"))
        for s in bank["sets"]:
            for q in s.get("qs", []):
                if q["dir"] == "ez":
                    out.add(q["p"])
                else:
                    out.add(q["a"][0])
                out.update(q.get("x", []))
            for t in s.get("terms", []):
                out.add(t["en"])
                if t.get("ex"):
                    out.add(t["ex"])
    return {g.key(t) for t in out if g.key(t)}


def collect(_targets):
    return {"interpret": {t: g.phrase_hash(t) for t in texts()}}, []


if __name__ == "__main__":
    g.collect = collect
    sys.argv = [sys.argv[0], "interpret"] + sys.argv[1:]
    asyncio.run(g.main())
