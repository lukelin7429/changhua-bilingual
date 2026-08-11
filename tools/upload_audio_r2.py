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
import argparse, concurrent.futures, json, pathlib, shutil, subprocess, sys
import urllib.request

BUCKET = "bilingual-schools-media"
PREFIX = "changhua-bilingual/learn/audio/"
PUBLIC_BASE = "https://changhua-bilingual.org/learn/audio/"


def wrangler_cmd():
    # A locally installed binary is far faster than npx, which pays Node start-up
    # plus a package-resolution round trip on every one of the 536 calls.
    local = pathlib.Path("worker/node_modules/.bin/wrangler")
    if local.exists():
        return [str(local)]
    if shutil.which("wrangler"):
        return ["wrangler"]
    if shutil.which("npx"):
        return ["npx", "--yes", "wrangler"]
    sys.exit("Neither wrangler nor npx found. Install Node, then: npx wrangler login")


def already_live(names, jobs):
    """Which clips are already reachable by a learner.

    wrangler has no way to list the objects in a bucket — `r2 object` is only
    get/put/delete and `r2 bucket list` lists buckets — so instead of asking R2
    what it holds, ask the site what it actually serves. That is the thing we
    care about anyway: an object present in the bucket but not reachable
    through the Worker is no use to anyone.
    """
    def head(name):
        # Cloudflare answers urllib's default User-Agent with a 403, so every
        # probe would look like a miss and the whole set would re-upload.
        req = urllib.request.Request(
            PUBLIC_BASE + name, method="HEAD",
            headers={"User-Agent": "changhua-bilingual-upload/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return name if r.status == 200 else None
        except Exception:                                # noqa: BLE001
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs * 3) as pool:
        return {n for n in pool.map(head, names) if n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="learn/audio")
    ap.add_argument("--force", action="store_true", help="re-upload even if present")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jobs", type=int, default=8,
                    help="parallel uploads (each is a separate wrangler call)")
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
    if args.force:
        skip = set()
    else:
        print(f"Checking which of the {len(files)} clips are already live…")
        skip = already_live([f.name for f in files], args.jobs)
        print(f"  {len(skip)} already served — skipping those.")

    todo = [f for f in files if f.name not in skip]
    if not todo:
        print("Nothing to upload — every clip is already live.")
        return
    print(f"{len(todo)} of {len(files)} to upload -> r2://{BUCKET}/{PREFIX}")
    if args.dry_run:
        for f in todo[:10]:
            print("  would upload", f.name)
        return

    def put(f):
        r = subprocess.run(
            w + ["r2", "object", "put", f"{BUCKET}/{PREFIX}{f.name}",
                 "--file", str(f), "--content-type", "audio/mpeg", "--remote"],
            capture_output=True, text=True,
        )
        return None if r.returncode == 0 else (f.name, (r.stderr or r.stdout).strip()[:140])

    failed, done = [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for res in pool.map(put, todo):
            done += 1
            if res:
                failed.append(res)
            if done % 50 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)}  ({len(failed)} failed)")

    if failed:
        print(f"\n{len(failed)} FAILED:")
        for n, err in failed[:10]:
            print(f"  {n}: {err}")
        sys.exit(1)
    print(f"\nDone. Verify with:\n"
          f"  curl -sI https://changhua-bilingual.org/learn/audio/{files[0].name} | head -3")


main()
