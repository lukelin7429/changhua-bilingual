#!/usr/bin/env python3
"""Generate natural-voice English clips for the site's 🔊 buttons.

Every page speaks through the browser's speechSynthesis, which sounds robotic
and different on every device. assets/js/voice.js intercepts those calls and
plays a clip from here whenever one exists for the text; anything without a
clip still goes to the device voice, so a missed sentence is never silent.

Texts come from the data-say / data-speak attributes of the pages given. Each
distinct text is one mp3 named by a hash of the text (same scheme as the
Mandarin clips in tools/gen_audio.py), so a sentence shared by many pages is
generated once and an edited sentence simply gets a new file.

Used for NEW pages only — pages published before 2026-10-30 keep the device
voice and are not backfilled. Run it on each new page with 🔊 buttons:

    python3 tools/gen_en_audio.py schools/<slug>/news/<story>/
    ./tools/upload_en_audio.sh                             # REQUIRED

Pipeline: edge-tts (Azure en-US neural voice) -> ffmpeg (trim silence,
normalise loudness, mono 48kbps).

Writes
    audio/en/<hash>.mp3          gitignored — these go to R2, not GitHub Pages
    audio/manifest/<site>.json   text -> hash — COMMIT IT
and adds the voice.js <script> tag to each page given (COMMIT the page too).
<site> is the school slug (schools/<slug>/…) or the top-level folder for hub
pages. voice.js loads only the manifest of the site it is on, so no page
downloads the whole site's list.

Requires: edge-tts, ffmpeg.
"""
import argparse, asyncio, hashlib, html, json, pathlib, re, shutil, sys

from gen_audio import phrase_hash, post

VOICE = "en-US-AvaMultilingualNeural"   # warm, clear US female. Alternatives:
                                        # en-US-AndrewMultilingualNeural (male),
                                        # en-US-EmmaMultilingualNeural
RATE = "-8%"            # a touch slower than natural; voice.js assumes this
                        # (CLIP_RATE there) when it honours each page's u.rate

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "audio" / "en"
MANIFESTS = ROOT / "audio" / "manifest"

SPOKEN = re.compile(r'data-(?:say|speak)="([^"]+)"')
VOICE_JS = ROOT / "assets" / "js" / "voice.js"
VOICE_TAG = re.compile(r'<script defer src="/assets/js/voice\.js(?:\?v=[0-9a-f]*)?"></script>')


def key(text: str) -> str:
    """The lookup key — must match key() in assets/js/voice.js."""
    return " ".join(html.unescape(text).split())


def site_of(page: pathlib.Path) -> str:
    parts = page.relative_to(ROOT).parts
    if parts[0] == "schools" and len(parts) > 2:
        return parts[1]
    return parts[0] if len(parts) > 1 else "home"


def collect(targets):
    """({site: {text: hash}}, [pages]) for every spoken text under the paths."""
    sites, spoken = {}, []
    for t in targets:
        t = (ROOT / t).resolve()
        pages = [t] if t.is_file() else sorted(t.rglob("*.html"))
        for page in pages:
            src = page.read_text(encoding="utf-8", errors="ignore")
            if "speechSynthesis" not in src:
                continue
            texts = sites.setdefault(site_of(page), {})
            for m in SPOKEN.finditer(src):
                text = key(m.group(1))
                if text:
                    texts[text] = phrase_hash(text)
            spoken.append(page)
    return sites, spoken


def add_voice_tag(page: pathlib.Path) -> bool:
    """Load voice.js on the page (or bump its ?v= to the current file)."""
    ver = hashlib.sha1(VOICE_JS.read_bytes()).hexdigest()[:8]
    tag = f'<script defer src="/assets/js/voice.js?v={ver}"></script>'
    src = page.read_text(encoding="utf-8")
    if VOICE_TAG.search(src):
        new = VOICE_TAG.sub(tag, src, count=1)
    elif "</body>" in src:
        new = src.replace("</body>", tag + "\n</body>", 1)
    else:
        return False
    if new != src:
        page.write_text(new, encoding="utf-8")
    return True


async def synth(text: str, dest: pathlib.Path, voice: str, tries: int = 3):
    import edge_tts
    for attempt in range(tries):
        try:
            await edge_tts.Communicate(text, voice, rate=RATE).save(str(dest))
            return
        except Exception:                           # noqa: BLE001
            if attempt == tries - 1:
                raise
            await asyncio.sleep(2 * (attempt + 1))


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="pages or folders to voice")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--jobs", type=int, default=4,
                    help="clips generated at once (edge-tts is network-bound)")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")

    sites, pages = collect(args.paths)
    todo = {}
    for texts in sites.values():
        for text, h in texts.items():
            if not (OUT / f"{h}.mp3").exists():
                todo[h] = text
    n_texts = sum(len(t) for t in sites.values())
    print(f"voice {args.voice} · rate {RATE} · {len(sites)} site(s) · "
          f"{n_texts} texts · {len(todo)} new clips -> {OUT.relative_to(ROOT)}")

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / ".raw"
    tmp.mkdir(exist_ok=True)
    gate = asyncio.Semaphore(args.jobs)
    failed, done = [], 0

    async def one(h, text):
        nonlocal done
        raw, dest = tmp / f"{h}.raw.mp3", OUT / f"{h}.mp3"
        async with gate:
            try:
                await synth(text, raw, args.voice)
                await asyncio.to_thread(post, raw, dest)
                raw.unlink()
            except Exception as e:                   # noqa: BLE001
                failed.append((h, text, repr(e)[:80]))
                return
        done += 1
        print(f"  [{done:>5}/{len(todo)}] {h}  {dest.stat().st_size:>6,}B  {text[:50]}")

    await asyncio.gather(*(one(h, t) for h, t in todo.items()))
    shutil.rmtree(tmp, ignore_errors=True)

    # Merge into each site's manifest: voicing one page must not drop the
    # entries other pages of the same school already rely on. Texts whose clip
    # failed stay out, so those buttons fall back to the device voice.
    bad = {h for h, _, _ in failed}
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    for site, texts in sorted(sites.items()):
        path = MANIFESTS / f"{site}.json"
        manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        manifest.update({t: h for t, h in texts.items() if h not in bad})
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=0, sort_keys=True) + "\n",
                        encoding="utf-8")
        print(f"  manifest {path.relative_to(ROOT)}: {len(manifest)} entries")

    for page in pages:
        if not add_voice_tag(page):
            print(f"  !! no </body> in {page.relative_to(ROOT)} — add the voice.js tag by hand")

    print("\n*** NOT DONE YET — the mp3s are only on this machine (audio/en/ is")
    print("    gitignored). Upload them, then commit the page(s) and manifest:")
    print("\n      ./tools/upload_en_audio.sh\n")
    if failed:
        print(f"\n{len(failed)} FAILED (left to the device voice):")
        for h, text, err in failed[:20]:
            print(f"  {h}  {text[:40]}  {err}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
