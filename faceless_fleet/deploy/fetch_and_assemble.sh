#!/usr/bin/env bash
# Run on the VPS (open egress). Downloads Higgsfield outputs + your Suno bed,
# then assembles the long-form video. This is the step that CANNOT run in the
# Claude web sandbox, whose egress policy blocks the Higgsfield CDN.
#
# Usage:
#   ./fetch_and_assemble.sh <channel> \
#       --video-url <higgsfield_clip_url> \
#       [--image-url <higgsfield_still_url>] \
#       --bed <path/to/suno_bed.wav> \
#       [--variant sleep]
#
# The Higgsfield URLs are the `rawUrl` values from each generation (Claude prints
# them, or read them in the Higgsfield app → generation → download link).
set -euo pipefail

CHANNEL="${1:?usage: fetch_and_assemble.sh <channel> --video-url URL --bed FILE}"; shift
VIDEO_URL=""; IMAGE_URL=""; BED=""; VARIANT="sleep"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --video-url) VIDEO_URL="$2"; shift 2;;
    --image-url) IMAGE_URL="$2"; shift 2;;
    --bed)       BED="$2"; shift 2;;
    --variant)   VARIANT="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 1;;
  esac
done

cd "$(dirname "$0")/../.."                      # repo root
RAW="faceless_fleet/output/raw/$CHANNEL"
mkdir -p "$RAW"

echo "[fetch] downloading assets -> $RAW"
[[ -n "$VIDEO_URL" ]] && curl -fSL "$VIDEO_URL" -o "$RAW/scene.mp4"
[[ -n "$IMAGE_URL" ]] && curl -fSL "$IMAGE_URL" -o "$RAW/scene.png"
if [[ -n "$BED" ]]; then cp "$BED" "$RAW/bed.wav"; else
  echo "[fetch] no --bed given; assemble will fail unless $RAW/bed.wav exists"; fi

# Minimal plan.json so assemble has a scene id + title if generate.py wasn't run here.
[[ -f "$RAW/plan.json" ]] || cat > "$RAW/plan.json" <<JSON
{"slug":"$CHANNEL","scene_id":"rainy_balcony","title":"she felt like home.","narration_enabled":false}
JSON

echo "[assemble] building long-form ($VARIANT)"
python3 -m faceless_fleet.pipeline.run assemble "$CHANNEL" --variant "$VARIANT"
echo "[done] review with: python3 -m faceless_fleet.pipeline.run review $CHANNEL"
