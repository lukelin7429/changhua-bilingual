#!/usr/bin/env bash
# One-time, per machine: create the `bilingual-media` rclone remote that
# tools/upload_audio.sh and tools/upload_en_audio.sh upload through.
# -----------------------------------------------------------------------------
# The keys are typed at the prompts below, not on the command line, so they
# never land in shell history.
#
# Get them from the Cloudflare dashboard → R2 → Manage API tokens →
# Create API token, with
#   permissions : Object Read & Write
#   bucket      : bilingual-schools-media
# The page that shows the keys also shows the Account ID (in the
# https://<ACCOUNT_ID>.r2.cloudflarestorage.com endpoint).
#
#   ./tools/setup_r2_remote.sh
set -euo pipefail

command -v rclone >/dev/null || { echo "rclone not installed — brew install rclone"; exit 1; }

read -rp  "Cloudflare Account ID : " ACCOUNT
read -rp  "Access Key ID         : " KEY
echo "(the secret is hidden while you type — paste it ONCE, then press Enter)"
read -rsp "Secret Access Key     : " SECRET; echo

# All three are plain hex: 32, 32 and 64 characters. Catch the usual slips —
# a field pasted twice, the cfat_… "Token value" instead of the S3 keys —
# before they are saved.
check() {
  [[ "$2" =~ ^[0-9a-f]{$3}$ ]] && return
  echo "  ✗ $1 should be $3 hex characters (got ${#2}). Nothing was saved — run this again."
  exit 1
}
check "Account ID"        "$ACCOUNT" 32
check "Access Key ID"     "$KEY"     32
check "Secret Access Key" "$SECRET"  64

rclone config create bilingual-media s3 \
  provider=Cloudflare \
  access_key_id="$KEY" secret_access_key="$SECRET" \
  endpoint="https://${ACCOUNT}.r2.cloudflarestorage.com" \
  acl=private no_check_bucket=true \
  --non-interactive >/dev/null

echo
echo "checking access to bilingual-schools-media ..."
if n=$(rclone lsf bilingual-media:bilingual-schools-media/changhua-bilingual/learn/audio 2>/dev/null | wc -l); then
  echo "  ok — the Mandarin clip folder has $(echo $n) files. Uploads will work."
else
  echo "  cannot read the bucket — check the Account ID and that the token covers bilingual-schools-media."
  exit 1
fi
