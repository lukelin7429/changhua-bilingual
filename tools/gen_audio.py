#!/usr/bin/env python3
"""Generate Mandarin audio for the Changhua learn app.

Every distinct `zh` phrase across the three Mandarin Challenge banks gets one
mp3, named by a hash of the phrase so identical phrases share a file and a
changed phrase gets a new name (safe to serve with immutable caching).

Pipeline: edge-tts (Azure zh-TW neural voice) -> ffmpeg (trim silence,
normalise loudness, mono 48kbps).

    python3 gen_audio.py --sample        # a hand-picked spread, for review
    python3 gen_audio.py                 # everything

Requires: edge-tts, ffmpeg.
"""
import argparse, asyncio, hashlib, json, pathlib, shutil, subprocess, sys

BANKS = ("beginner", "intermediate", "advanced")
VOICE = "zh-TW-HsiaoChenNeural"   # Taiwanese Mandarin, female. Alternatives:
                                  # zh-TW-YunJheNeural (male), zh-TW-HsiaoYuNeural
RATE = "-10%"                     # a touch slower than natural, for learners

# Hand-picked review set: one of each level and question type, short and long.
SAMPLE_IDS = ["B001", "B017", "B050", "B123",
              "I019", "I111", "I162",
              "A011", "A090", "A163"]


def phrase_hash(zh: str) -> str:
    return hashlib.sha1(zh.encode("utf-8")).hexdigest()[:12]


TERMS = pathlib.Path("culture/data/terms.json")        # School Culture vocabulary
EXPLORE = pathlib.Path("explore/data/phrases.json")    # Explore travel phrases


def load_phrases(data_dir: pathlib.Path):
    """Every phrase needing audio, de-duplicated by content hash.

    All three apps draw from one pool: a phrase shared between the Mandarin
    banks, the School Culture terms (教務處, 導師 …) and the Explore travel
    phrases is one file, used by all of them.
    """
    seen, order = {}, []

    def add(zh, py, ref):
        h = phrase_hash(zh)
        if h not in seen:
            seen[h] = {"hash": h, "zh": zh, "py": py, "ids": []}
            order.append(h)
        seen[h]["ids"].append(ref)

    for name in BANKS:
        bank = json.loads((data_dir / f"{name}.json").read_text(encoding="utf-8"))
        for q in bank["questions"]:
            add(q["zh"], q["py"], q["id"])

    if TERMS.exists():
        for t in json.loads(TERMS.read_text(encoding="utf-8"))["terms"]:
            add(t["zh"], t["py"], "term:" + t["zh"])

    if EXPLORE.exists():
        for p in json.loads(EXPLORE.read_text(encoding="utf-8"))["phrases"]:
            add(p["zh"], p["py"], "explore:" + p["chapter"])

    return [seen[h] for h in order]


async def synth(zh: str, dest: pathlib.Path, voice: str):
    import edge_tts
    await edge_tts.Communicate(zh, voice, rate=RATE).save(str(dest))


def post(raw: pathlib.Path, out: pathlib.Path):
    """Trim silence at both ends, normalise loudness, encode mono 48k."""
    trim = ("silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
            "areverse,"
            "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
            "areverse")
    af = f"{trim},loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=0.15"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
         "-af", af, "-ac", "1", "-ar", "44100", "-b:a", "48k", str(out)],
        check=True,
    )


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="fets/mandarin-challenge/data")
    ap.add_argument("--out", default="learn/audio")
    ap.add_argument("--sample", action="store_true",
                    help="only the hand-picked review set")
    ap.add_argument("--voice", default=VOICE)
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")

    data_dir = pathlib.Path(args.data)
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / ".raw"
    tmp.mkdir(exist_ok=True)

    phrases = load_phrases(data_dir)
    if args.sample:
        wanted = set(SAMPLE_IDS)
        phrases = [p for p in phrases if wanted & set(p["ids"])]

    print(f"voice {args.voice} · rate {RATE} · {len(phrases)} phrases -> {out_dir}")
    manifest, failed, total = {}, [], 0

    for i, p in enumerate(phrases, 1):
        dest = out_dir / f"{p['hash']}.mp3"
        manifest[p["zh"]] = p["hash"]
        if dest.exists():
            total += dest.stat().st_size
            continue
        raw = tmp / f"{p['hash']}.raw.mp3"
        try:
            await synth(p["zh"], raw, args.voice)
            post(raw, dest)
            raw.unlink()
        except Exception as e:                       # noqa: BLE001
            failed.append((p["hash"], p["zh"], repr(e)[:80]))
            continue
        size = dest.stat().st_size
        total += size
        print(f"  [{i:>3}/{len(phrases)}] {p['hash']}  {size:>6,}B  "
              f"{p['zh'][:18]:<18} {p['ids'][0]}")

    (out_dir.parent / "audio-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=0, sort_keys=True) + "\n",
        encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n*** learn/audio-manifest.json rewritten with {len(manifest)} entries — "
          f"COMMIT IT. The apps look phrases up here; an uncommitted manifest "
          f"means new clips resolve to undefined.mp3 and 404 in production. ***")
    print(f"\n{len(manifest) - len(failed)} files · {total/1024/1024:.1f} MB total · "
          f"{total/max(1, len(manifest) - len(failed))/1024:.1f} KB average")
    if failed:
        print(f"\n{len(failed)} FAILED:")
        for h, zh, err in failed[:20]:
            print(f"  {h}  {zh}  {err}")
        sys.exit(1)


asyncio.run(main())
