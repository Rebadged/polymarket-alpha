"""Plan a budgeted batch of clips to generate (the periodic restock).

Computes which scene x location clips are MISSING from a channel's library and
writes a manifest (still + motion prompts + target filename) capped by a credit
budget. A Higgsfield-capable agent (Cowork, or this assistant) then fulfils it:
generate still -> animate -> download to target_dir/<clip_name>. See
deploy/COWORK_RESTOCK.md.

Usage:
  python -m faceless_fleet.pipeline.run batch-plan rain_cabin --budget 160
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from . import generate
from .config import ROOT, load_channel


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "loc"


def plan(slug: str, budget_credits: float = 160) -> dict:
    cfg = load_channel(slug)
    per = cfg["generation"].get("est_credits_per_clip", 9)
    iters = cfg["generation"].get("iteration_factor", 3)
    # Plan on the RAW per-clip cost (optimistic): the fulfiller watches the live balance and
    # stops re-rolling when it runs low, so we don't want to under-plan the work-list. The
    # worst-case (with re-rolls) is reported below so spend never surprises.
    max_new = max(1, int(budget_credits // per))
    clips_dir = ROOT / cfg.get("auto", {}).get("clips_dir", "assets/clips") / slug
    existing = {p.stem for p in clips_dir.glob("*.mp4")} if clips_dir.exists() else set()
    locs = cfg.get("location_pool") or [{"title": "", "prompt": ""}]

    items = []
    for scene in cfg["scene_pool"]:
        for loc in locs:
            name = f"{scene['id']}__{_slug(loc.get('title',''))}"
            if name in existing:
                continue
            tokens = generate._tokens(cfg, loc.get("title", ""))
            still = generate._fmt(scene["still_prompt"], tokens)
            if loc.get("prompt"):
                still += f", set {loc['prompt']}"
            still += " -- " + cfg["identity"]["negative"]
            items.append({
                "clip_name": f"{name}.mp4",
                "image_model": cfg["generation"]["image_model"],
                "video_model": cfg["generation"]["video_model"],
                "duration": cfg["generation"].get("clip_seconds", 10),
                "aspect_ratio": cfg["generation"].get("aspect_ratio", "16:9"),
                "still_prompt": still,
                "motion_prompt": generate._fmt(scene["motion_prompt"], tokens),
            })
            if len(items) >= max_new:
                break
        if len(items) >= max_new:
            break

    manifest = {
        "slug": slug, "budget_credits": budget_credits,
        "est_credits_per_clip": per, "iteration_factor": iters,
        "count": len(items),
        "est_credits_clean": len(items) * per,               # if every gen lands first try
        "est_credits_worst_case": len(items) * per * iters,  # with full re-rolls
        "target_dir": str(clips_dir), "items": items,
    }
    clips_dir.mkdir(parents=True, exist_ok=True)
    (clips_dir / "_to_generate.json").write_text(json.dumps(manifest, indent=2))
    print(f"[batch-plan] {slug}: {len(items)} clips to generate "
          f"(~{len(items)*per} cr if clean / up to ~{len(items)*per*iters} cr with {iters}x re-rolls) "
          f"-> {clips_dir/'_to_generate.json'}")
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("--budget", type=float, default=160)
    args = ap.parse_args()
    plan(args.channel, args.budget)
