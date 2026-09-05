"""The zero-touch daily loop: pick an unused clip from the library, build the
audio bed, assemble to long-form, (optionally) approve, and schedule-upload.

No manual paths or filenames — this is what runs on the VPS cron. Prereqs that
get stocked OCCASIONALLY (not per-run):
  - a clip library:  assets/clips/<slug>/<scene_id>__*.mp4   (generated in batches)
  - the SFX library: assets/sfx/*.mp3                        (fetch-sfx, one time)

Usage:
  python -m faceless_fleet.pipeline.run auto rain_cabin                 # assemble + approve, leave for upload
  python -m faceless_fleet.pipeline.run auto rain_cabin --publish       # also upload (private + jittered publishAt)
  python -m faceless_fleet.pipeline.run auto rain_cabin --variant 3h --no-approve
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from . import assemble as assemble_mod
from . import generate, review, state, upload
from .config import ROOT, load_channel, output_dirs


def clips_dir(cfg: dict) -> Path:
    return ROOT / cfg.get("auto", {}).get("clips_dir", "assets/clips") / cfg["_slug"]


def pick_clip(cfg: dict, scene_id: str, st: dict) -> Path | None:
    """Least-recently-used unused clip whose filename starts with the scene id."""
    d = clips_dir(cfg)
    if not d.exists():
        return None
    candidates = sorted(d.glob(f"{scene_id}__*.mp4")) or sorted(d.glob(f"{scene_id}*.mp4"))
    if not candidates:
        return None
    used = st.get("used_clips", [])
    fresh = [c for c in candidates if c.name not in used]
    return fresh[0] if fresh else candidates[0]


def auto(slug: str, variant: str = "8h", approve: bool = True, publish: bool = False) -> dict:
    cfg = load_channel(slug)
    dirs = output_dirs(cfg)
    st = state.load(slug)

    scene = state.next_scene(cfg, st)
    location = state.next_location(cfg, st)
    loc_title = location["title"] if isinstance(location, dict) else ""
    tokens = generate._tokens(cfg, loc_title)
    title = generate.choose_title(cfg, scene, st, tokens)

    clip = pick_clip(cfg, scene["id"], st)
    if not clip:
        raise FileNotFoundError(
            f"No clips for scene '{scene['id']}' in {clips_dir(cfg)}. "
            f"Stock the clip library first (batch-generate + download).")

    # stage the chosen clip as this run's scene.mp4 + write the plan
    raw = dirs["raw"]
    shutil.copy(str(clip), str(raw / "scene.mp4"))
    plan = {
        "slug": slug, "scene_id": scene["id"], "weather": scene.get("weather", ""),
        "audio_hint": scene.get("audio_hint", ""), "location": loc_title,
        "title": title, "narration_enabled": cfg.get("narration", {}).get("enabled", False),
    }
    (raw / "plan.json").write_text(json.dumps(plan, indent=2))

    out = assemble_mod.assemble(slug, variant)
    print(f"[auto] {slug}: scene={scene['id']} clip={clip.name} -> {out.name}")

    st.setdefault("used_clips", []).append(clip.name)
    st["used_clips"] = st["used_clips"][-200:]
    state.record(slug, st, scene["id"], title, loc_title)

    if approve:
        out = review.approve(slug, out.name)
    if publish:
        upload.upload_one(slug, out, dry_run=False)
    return {"video": str(out), "title": title, "scene": scene["id"], "clip": clip.name}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("--variant", default="8h")
    ap.add_argument("--no-approve", dest="approve", action="store_false")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()
    auto(args.channel, args.variant, approve=args.approve, publish=args.publish)
