#!/usr/bin/env python3
"""Upload the /learn/ pronunciation clips to Cloudflare R2.

The clips are deliberately kept out of git and out of the Pages artifact — the
Worker in worker/ serves them straight from R2. Object keys follow the same
convention the schools photos already use:

    changhua-bilingual/learn/audio/<hash>.mp3

Needs wrangler and a logged-in Cloudflare session:

    npm install -g wrangler        # or use npx below
    npx wrangler login
    python3 tools/upload_audio_r2.py

Re-running is safe: objects already present are skipped unless --force.
"""
import argparse, json, pathlib, shutil, subprocess, sys

BUCKET = "bilingual-schools-media"
PREFIX = "changhua-bilingual/learn/audio/"


def wrangler_cmd():
    if shutil.which("wrangler"):
        return ["wrangler"]
    if shutil.which("npx"):
        return ["npx", "--yes", "wrangler"]
    sys.exit("Neither wrangler nor npx found. Install Node, then: npx wrangler login")


def existing_keys(w):
    """Keys already in the bucket, so a re-run doesn't re-upload everything."""
    try:
        out = subprocess.run(
            w + ["r2", "object", "list", BUCKET, "--prefix", PREFIX, "--remote"],
            capture_output=True, text=True, timeout=180,
        )
        if out.returncode != 0:
            return None
        return {ln.strip() for ln in out.stdout.splitlines() if ln.strip().endswith(".mp3")}
    except Exception:                                    # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="learn/audio")
    ap.add_argument("--force", action="store_true", help="re-upload even if present")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = pathlib.Path(args.dir)
    files = sorted(src.glob("*.mp3"))
    if not files:
        sys.exit(f"No mp3 files in {src} — run tools/gen_audio.py first.")

    manifest = json.loads(pathlib.Path("learn/audio-manifest.json").read_text(encoding="utf-8"))
    wanted = set(manifest.values())
    have = {f.stem for f in files}
    missing = wanted - have
    if missing:
        sys.exit(f"{len(missing)} clips in the manifest have no file "
                 f"(e.g. {sorted(missing)[:3]}). Run tools/gen_audio.py first.")

    w = wrangler_cmd()
    skip = set() if args.force else (existing_keys(w) or set())
    if skip:
        print(f"{len(skip)} objects already in R2 — skipping those.")

    todo = [f for f in files if (PREFIX + f.name) not in skip]
    print(f"{len(todo)} of {len(files)} to upload -> r2://{BUCKET}/{PREFIX}")
    if args.dry_run:
        for f in todo[:10]:
            print("  would upload", f.name)
        return

    failed = []
    for i, f in enumerate(todo, 1):
        key = PREFIX + f.name
        r = subprocess.run(
            w + ["r2", "object", "put", f"{BUCKET}/{key}",
                 "--file", str(f), "--content-type", "audio/mpeg", "--remote"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            failed.append((f.name, (r.stderr or r.stdout).strip()[:120]))
        if i % 25 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)}")

    if failed:
        print(f"\n{len(failed)} FAILED:")
        for n, err in failed[:10]:
            print(f"  {n}: {err}")
        sys.exit(1)
    print(f"\nDone. Verify with:\n"
          f"  curl -sI https://changhua-bilingual.org/learn/audio/{files[0].name} | head -3")


main()
