#!/bin/bash
# Walk Zhongzheng photos, resize anything wider than 1800px or heavier
# than 600 KB down to max 1600w @ 80% JPEG quality (in place).
# Skip clubs/* — those are low-res video frames; resizing them would just
# add JPEG artefacts on top of bad source data. Skip logo and favicons.
#
# Run idempotently; re-running on already-small files is a no-op.

set -e
REPO_PHOTOS="$HOME/Documents/Claude/repos/changhua-bilingual/schools/zhongzheng/photos"
MAX_W=1600
QUALITY=80
SIZE_THRESHOLD_KB=600
WIDTH_THRESHOLD=1800

total_before=0
total_after=0
processed=0
skipped=0

while IFS= read -r f; do
    rel="${f#$REPO_PHOTOS/}"
    # Skip logo, favicons, clubs/* (low-res)
    case "$rel" in
        logo.jpg|favicon*|clubs/*) skipped=$((skipped + 1)); continue ;;
    esac

    width=$(sips -g pixelWidth "$f" 2>/dev/null | awk '/pixelWidth/{print $2}')
    sz_kb=$(stat -f %z "$f" | awk '{print int($1/1024)}')
    total_before=$((total_before + sz_kb))

    needs_resize=0
    [ -n "$width" ] && [ "$width" -gt "$WIDTH_THRESHOLD" ] && needs_resize=1
    [ "$sz_kb" -gt "$SIZE_THRESHOLD_KB" ] && needs_resize=1

    # Skip PNGs (no in-place quality reduction with sips); convert separately if needed
    case "$f" in
        *.png|*.PNG)
            if [ "$needs_resize" = "1" ]; then
                # Convert PNG → JPG in place (replace extension), but keep original path the same
                # Actually rename: file.png → file.jpg
                tmp_jpg="${f%.*}.jpg"
                sips -s format jpeg -s formatOptions "$QUALITY" -Z "$MAX_W" "$f" --out "$tmp_jpg" >/dev/null 2>&1
                # only rm if .jpg actually written
                if [ -f "$tmp_jpg" ] && [ "$f" != "$tmp_jpg" ]; then
                    rm -f "$f"
                    echo "  ✎ PNG→JPG: $rel  →  ${rel%.*}.jpg"
                    processed=$((processed + 1))
                    sz_after=$(stat -f %z "$tmp_jpg" | awk '{print int($1/1024)}')
                    total_after=$((total_after + sz_after))
                    continue
                fi
            fi
            total_after=$((total_after + sz_kb))
            continue
            ;;
    esac

    if [ "$needs_resize" = "1" ]; then
        sips -Z "$MAX_W" -s formatOptions "$QUALITY" "$f" --out "$f" >/dev/null 2>&1
        sz_after=$(stat -f %z "$f" | awk '{print int($1/1024)}')
        total_after=$((total_after + sz_after))
        new_w=$(sips -g pixelWidth "$f" 2>/dev/null | awk '/pixelWidth/{print $2}')
        echo "  ↓ $rel: ${width}w/${sz_kb}KB → ${new_w}w/${sz_after}KB"
        processed=$((processed + 1))
    else
        total_after=$((total_after + sz_kb))
        skipped=$((skipped + 1))
    fi
done < <(find "$REPO_PHOTOS" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \))

echo ""
echo "=== Summary ==="
echo "  Processed: $processed   Skipped: $skipped"
echo "  Total before: ${total_before} KB ($((total_before/1024)) MB)"
echo "  Total after:  ${total_after} KB ($((total_after/1024)) MB)"
saved=$((total_before - total_after))
echo "  Saved:        ${saved} KB ($((saved/1024)) MB)"
