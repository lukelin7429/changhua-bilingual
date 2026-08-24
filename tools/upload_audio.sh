#!/usr/bin/env bash
# Publish the Mandarin pronunciation clips to R2.
# -----------------------------------------------------------------------------
# learn/audio/ is gitignored — the mp3s are NOT deployed by pushing to main.
# worker/worker.js serves /learn/audio/<hash>.mp3 straight from the R2 bucket,
# with no origin copy, so a clip that is not uploaded is a hard 404 and the apps
# fall back to the device's own (much worse) voice.
#
# Run this after every `python3 tools/gen_audio.py`.
#
#   ./tools/upload_audio.sh            # upload anything missing, then verify
#   ./tools/upload_audio.sh --dry-run  # show what would be uploaded
#
# Requires: rclone with the `bilingual-media` remote (Cloudflare R2).
set -euo pipefail

REMOTE="bilingual-media"
BUCKET="bilingual-schools-media"
PREFIX="changhua-bilingual/learn/audio"
LOCAL="learn/audio"
MANIFEST="learn/audio-manifest.json"
DEST="${REMOTE}:${BUCKET}/${PREFIX}"

cd "$(dirname "$0")/.."

command -v rclone >/dev/null || { echo "rclone not installed — brew install rclone"; exit 1; }
[ -d "$LOCAL" ]     || { echo "$LOCAL missing — run tools/gen_audio.py first"; exit 1; }
[ -f "$MANIFEST" ]  || { echo "$MANIFEST missing — run tools/gen_audio.py first"; exit 1; }

if ! rclone lsf "$DEST" >/dev/null 2>&1; then
  echo "Cannot reach $DEST."
  echo "Check the 'bilingual-media' remote in ~/.config/rclone/rclone.conf (R2 token may have expired)."
  exit 1
fi

local_n=$(find "$LOCAL" -name '*.mp3' | wc -l | tr -d ' ')
echo "local  : $local_n mp3 in $LOCAL"
echo "remote : $(rclone lsf "$DEST" | wc -l | tr -d ' ') mp3 in $DEST"

if [ "${1:-}" = "--dry-run" ]; then
  echo
  echo "would upload:"
  rclone copy "$LOCAL" "$DEST" --include '*.mp3' --no-update-modtime --dry-run 2>&1 | sed 's/^/  /'
  exit 0
fi

echo
rclone copy "$LOCAL" "$DEST" --include '*.mp3' --no-update-modtime --progress

# ---- verify: every hash the apps will ask for must exist in the bucket -------
echo
echo "verifying every manifest entry is present in R2 ..."
rclone lsf "$DEST" | sed 's/\.mp3$//' | sort > /tmp/_r2_hashes.txt
python3 - <<'PY'
import json, pathlib, sys
man = json.load(open("learn/audio-manifest.json"))
have = set(pathlib.Path("/tmp/_r2_hashes.txt").read_text().split())
missing = sorted({h for h in man.values() if h not in have})
print(f"  manifest entries : {len(man)}")
print(f"  present in R2    : {len(man) - len(missing)}")
if missing:
    print(f"\n  *** {len(missing)} MISSING — these will 404 and fall back to the device voice:")
    for h in missing[:20]:
        zh = next((k for k, v in man.items() if v == h), "?")
        print(f"    {h}  {zh}")
    sys.exit(1)
print("\n  all clips live. Remember to commit learn/audio-manifest.json if it changed.")
PY
