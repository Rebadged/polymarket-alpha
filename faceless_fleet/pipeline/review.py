"""The human quality gate + automated policy checks.

Videos land in output/pending_review/<slug>/. You (or a Claude review session)
inspect them, then `approve` moves them to output/approved/<slug>/ where the
uploader will pick them up. `check` runs the automatable policy guards before a
human ever looks, so obvious violations never reach the queue.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from . import state
from .config import load_channel, output_dirs


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def policy_check(slug: str, video: Path) -> list[str]:
    """Return a list of policy warnings. Empty list = passes automated checks."""
    cfg = load_channel(slug)
    st = state.load(slug)
    warnings: list[str] = []

    dur = ffprobe_duration(video)
    if dur < 8 * 60:
        warnings.append(f"duration {dur/60:.1f}min < 8min (no mid-rolls; weak for ambient).")

    # Variation guard: scene id is embedded in the filename "slug__scene__variant.mp4"
    parts = video.stem.split("__")
    scene_id = parts[1] if len(parts) > 2 else "?"
    recent = st.get("history", [])[-3:-1]  # the couple before this one
    if cfg["policy"].get("require_distinct_from_last") and scene_id in [h["scene"] for h in recent]:
        warnings.append(f"scene '{scene_id}' matches a very recent upload — vary it (inauthentic-content risk).")

    if cfg["metadata"].get("made_for_kids"):
        warnings.append("made_for_kids=true cripples monetization (COPPA). Confirm this is intended.")
    return warnings


def review_queue(slug: str) -> None:
    cfg = load_channel(slug)
    dirs = output_dirs(cfg)
    vids = sorted(dirs["pending_review"].glob("*.mp4"))
    if not vids:
        print(f"[review] nothing pending for {slug}")
        return
    print(f"[review] {len(vids)} pending for {slug}:")
    for v in vids:
        warns = policy_check(slug, v)
        flag = "  ⚠ " + " | ".join(warns) if warns else "  ✓ passes automated checks"
        print(f"  - {v.name}\n{flag}")


def approve(slug: str, filename: str) -> Path:
    cfg = load_channel(slug)
    dirs = output_dirs(cfg)
    src = dirs["pending_review"] / filename
    if not src.exists():
        raise FileNotFoundError(src)
    warns = policy_check(slug, src)
    if warns:
        print("[review] WARNINGS (approving anyway, your call):")
        for w in warns:
            print("   ⚠", w)
    dest = dirs["approved"] / filename
    shutil.move(str(src), str(dest))
    # carry the plan alongside so the uploader has the metadata
    plan = dirs["raw"] / "plan.json"
    if plan.exists():
        shutil.copy(str(plan), str(dest.with_suffix(".plan.json")))
    print(f"[review] approved -> {dest}")
    return dest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("action", choices=["list", "approve"])
    ap.add_argument("--file", help="filename to approve")
    args = ap.parse_args()
    if args.action == "list":
        review_queue(args.channel)
    else:
        approve(args.channel, args.file)
