"""Weekly fleet orchestrator — the set-and-forget job.

For every CONNECTED channel (its YouTube refresh-token env var is set), produce +
schedule that channel's week of videos from the existing clip library: pick clip →
mix seasonal audio bed → assemble → upload PRIVATE with a jittered publishAt.

This is 100% deterministic (no agent, no tokens) → it runs straight on VPS cron.
Generating NEW clips (the one step that needs Higgsfield) is a SEPARATE periodic
restock — see deploy/COWORK_RESTOCK.md (Cowork) or generation.backend=rest (API).

Usage:
  python -m faceless_fleet.pipeline.run weekly                 # all connected channels
  python -m faceless_fleet.pipeline.run weekly --channels rain_cabin --dry-run
"""
from __future__ import annotations

import argparse
import os
import traceback

from . import auto
from .config import list_channels, load_channel


def _connected(cfg: dict) -> bool:
    """A channel is live once its per-channel refresh token is in the environment."""
    return bool(os.environ.get(cfg["channel"]["oauth_secret_env"]))


def run_week(channels: list[str] | None = None, publish: bool = True) -> dict:
    channels = channels or list_channels()
    summary = {}
    for slug in channels:
        cfg = load_channel(slug)
        if publish and not _connected(cfg):
            print(f"[weekly] skip {slug}: not connected (no {cfg['channel']['oauth_secret_env']})")
            summary[slug] = "skipped (not connected)"
            continue
        n = cfg.get("cadence", {}).get("uploads_per_week", 3)
        variant = cfg.get("auto", {}).get("default_variant", "8h")
        made = 0
        for i in range(n):
            try:
                auto.auto(slug, variant=variant, approve=True, publish=publish)
                made += 1
            except Exception as e:                       # one bad run never kills the week
                print(f"[weekly] {slug} #{i+1}/{n} failed: {e}")
                traceback.print_exc()
        summary[slug] = f"{made}/{n} scheduled"
        print(f"[weekly] {slug}: {summary[slug]}")
    print(f"[weekly] done: {summary}")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", nargs="*")
    ap.add_argument("--dry-run", action="store_true", help="assemble + approve but do not upload")
    args = ap.parse_args()
    run_week(args.channels, publish=not args.dry_run)
