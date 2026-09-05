#!/usr/bin/env bash
# VPS runtime for one channel: generate -> (fulfil) -> assemble -> leave in pending_review.
# This is the HEAVY path; run it on the Chicago VPS, not on CI runners.
#
# Usage:  ./run_channel.sh <channel_slug> [variant]
# Env:    HIGGSFIELD_API_KEY (only if generation backend=rest)
set -euo pipefail

CHANNEL="${1:?usage: run_channel.sh <channel> [variant]}"
VARIANT="${2:-3h}"
cd "$(dirname "$0")/../.."          # repo root

export PYTHONUNBUFFERED=1

echo "[$(date -u +%FT%TZ)] generate $CHANNEL"
python3 -m faceless_fleet.pipeline.run generate "$CHANNEL"

# If backend=manifest, a Claude Code/MCP session (or headless `claude -p`) must
# fulfil output/raw/<channel>/jobs.json before assembly. With backend=rest the
# generate step already produced the raw assets, so we proceed straight through.
RAW="faceless_fleet/output/raw/$CHANNEL"
if [[ ! -f "$RAW/scene.mp4" && ! -f "$RAW/scene.png" ]]; then
  echo "[run_channel] raw assets not present yet — fulfil $RAW/jobs.json via MCP, then re-run assemble."
  exit 0
fi

echo "[$(date -u +%FT%TZ)] assemble $CHANNEL ($VARIANT)"
python3 -m faceless_fleet.pipeline.run assemble "$CHANNEL" --variant "$VARIANT"

echo "[$(date -u +%FT%TZ)] done -> review with: python3 -m faceless_fleet.pipeline.run review $CHANNEL"
