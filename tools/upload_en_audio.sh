#!/usr/bin/env bash
# Publish the English 🔊 clips to R2.
# -----------------------------------------------------------------------------
# audio/en/ is gitignored — the mp3s are NOT deployed by pushing to main.
# worker/worker.js serves /audio/en/<hash>.mp3 straight from the R2 bucket,
# with no origin copy, so a clip that is not uploaded is a hard 404 and the
# page falls back to the device's own (robotic) voice.
#
# Run this after every `python3 tools/gen_en_audio.py <page>`, then commit the
# page and audio/manifest/<site>.json.
#
#   ./tools/upload_en_audio.sh            # upload anything missing, then verify
#   ./tools/upload_en_audio.sh --dry-run  # show what would be uploaded
#
# Requires: rclone with the `bilingual-media` remote (Cloudflare R2).
set -euo pipefail

REMOTE="bilingual-media"
BUCKET="bilingual-schools-media"
PREFIX="changhua-bilingual/audio/en"
LOCAL="audio/en"
MANIFESTS="audio/manifest"
DEST="${REMOTE}:${BUCKET}/${PREFIX}"

cd "$(dirname "$0")/.."

command -v rclone >/dev/null || { echo "rclone not installed — brew install rclone"; exit 1; }
[ -d "$LOCAL" ]     || { echo "$LOCAL missing — run tools/gen_en_audio.py first"; exit 1; }
[ -d "$MANIFESTS" ] || { echo "$MANIFESTS missing — run tools/gen_en_audio.py first"; exit 1; }

# Check the bucket, not $DEST: before the first upload audio/en/ does not exist yet.
if ! rclone lsf "${REMOTE}:${BUCKET}/changhua-bilingual" --max-depth 1 >/dev/null 2>&1; then
  echo "Cannot reach ${REMOTE}:${BUCKET}."
  echo "Check the 'bilingual-media' remote (R2 token may have expired) — set it up with ./tools/setup_r2_remote.sh"
  exit 1
fi

echo "local  : $(find "$LOCAL" -name '*.mp3' | wc -l | tr -d ' ') mp3 in $LOCAL"
echo "remote : $(rclone lsf "$DEST" 2>/dev/null | wc -l | tr -d ' ') mp3 in $DEST"

if [ "${1:-}" = "--dry-run" ]; then
  echo
  echo "would upload:"
  rclone copy "$LOCAL" "$DEST" --include '*.mp3' --no-update-modtime --dry-run 2>&1 | sed 's/^/  /'
  exit 0
fi

echo
rclone copy "$LOCAL" "$DEST" --include '*.mp3' --no-update-modtime --progress

# ---- verify: every hash any page will ask for must exist in the bucket -------
echo
echo "verifying every manifest entry is present in R2 ..."
HAVE=$(mktemp)
trap 'rm -f "$HAVE"' EXIT
rclone lsf "$DEST" | sed 's/\.mp3$//' | sort > "$HAVE"
python3 - "$HAVE" "$MANIFESTS" <<'PY'
import json, pathlib, sys
have = set(pathlib.Path(sys.argv[1]).read_text().split())
missing, total = [], 0
for path in sorted(pathlib.Path(sys.argv[2]).glob("*.json")):
    man = json.loads(path.read_text(encoding="utf-8"))
    total += len(man)
    missing += [(path.stem, h, t) for t, h in man.items() if h not in have]
print(f"  manifest entries : {total}")
print(f"  present in R2    : {total - len(missing)}")
if missing:
    print(f"\n  *** {len(missing)} MISSING — these will 404 and fall back to the device voice:")
    for site, h, text in missing[:20]:
        print(f"    {site:<12} {h}  {text[:50]}")
    sys.exit(1)
print("\n  all clips live. Now commit the page(s) and audio/manifest/*.json.")
PY
