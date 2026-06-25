"""Stage 2 — deterministic assembly with ffmpeg.

Turns the raw assets (scene.png / scene.mp4 / bed.wav / narration.wav) into a
finished long-form video in output/pending_review/<slug>/.

Key ffmpeg techniques (from the research playbook):
  - stream_loop   : loop a short clip to N hours with NO re-encode (fast, lossless)
  - zoompan       : Ken Burns slow-zoom to give a single still gentle motion
  - acrossfade    : seamless audio loop seam
  - amix + volume : duck a music bed under narration

This module is pure ffmpeg, runs anywhere (VPS, Actions, locally), needs no
credits, and is independently testable.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .config import load_channel, output_dirs

HOURS = {"1h": 3600, "3h": 10800, "8h": 28800}


def _run(cmd: list[str]) -> None:
    print("[ffmpeg]", " ".join(str(c) for c in cmd[:6]), "...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def kenburns_from_still(still: Path, out: Path, cfg: dict, seconds: int) -> Path:
    """Make a gently zooming clip from a single still (fallback when there's no motion clip)."""
    a = cfg["assembly"]
    frames = seconds * a["fps"]
    zoom = f"zoompan=z='min(zoom+{a['kenburns_zoom_per_frame']},{a['kenburns_max_zoom']})'" \
           f":d={frames}:s={a['width']}x{a['height']}:fps={a['fps']}"
    _run(["ffmpeg", "-y", "-loop", "1", "-i", str(still),
          "-vf", zoom, "-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
    return out


def loop_to_length(clip: Path, out: Path, seconds: int) -> Path:
    """stream_loop the source clip up to `seconds` with no re-encode."""
    _run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(clip),
          "-t", str(seconds), "-c", "copy", str(out)])
    return out


def loop_audio(bed: Path, out: Path, seconds: int, crossfade: int) -> Path:
    """Loop a music bed to length WITHOUT re-encoding the whole thing.

    Encode the short bed to AAC once, then stream_loop -c copy to the target
    length. A 3h loop then takes ~a second instead of re-encoding 3h of audio."""
    unit = out.with_name("_bed_unit.m4a")
    _run(["ffmpeg", "-y", "-i", str(bed), "-c:a", "aac", "-b:a", "192k", str(unit)])
    _run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(unit),
          "-t", str(seconds), "-c", "copy", str(out)])
    return out


def mix_narration_over_bed(narration: Path, bed: Path, out: Path, bed_gain: float) -> Path:
    fc = (f"[0:a]volume=1.0[n];[1:a]volume={bed_gain}[b];"
          f"[n][b]amix=inputs=2:duration=longest[out]")
    _run(["ffmpeg", "-y", "-i", str(narration), "-i", str(bed),
          "-filter_complex", fc, "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out)])
    return out


def mux(video: Path, audio: Path, out: Path) -> Path:
    """Combine looped video + looped audio, ending at the shorter stream.
    Both inputs are already encoded, so copy both streams = near-instant mux."""
    _run(["ffmpeg", "-y", "-i", str(video), "-i", str(audio),
          "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
          "-shortest", "-movflags", "+faststart", str(out)])
    return out


def assemble(slug: str, variant: str = "3h") -> Path:
    cfg = load_channel(slug)
    dirs = output_dirs(cfg)
    raw = dirs["raw"]
    plan = json.loads((raw / "plan.json").read_text()) if (raw / "plan.json").exists() else {}

    seconds = HOURS.get(variant, HOURS["3h"])
    a = cfg["assembly"]
    work = raw / "_work"
    work.mkdir(exist_ok=True)

    # --- video base: prefer the motion clip, else Ken Burns the still ---
    if (raw / "scene.mp4").exists():
        base_clip = raw / "scene.mp4"
    elif (raw / "scene.png").exists():
        base_clip = kenburns_from_still(raw / "scene.png", work / "kenburns.mp4", cfg, 20)
    else:
        raise FileNotFoundError(
            f"No scene.mp4 or scene.png in {raw}. Fulfill the generation manifest first."
        )
    looped_v = loop_to_length(base_clip, work / "video_long.mp4", seconds)

    # --- audio base ---
    bed = raw / "bed.wav"
    if not bed.exists():
        raise FileNotFoundError(f"No bed.wav in {raw}.")
    looped_a = loop_audio(bed, work / "audio_long.m4a", seconds, a["crossfade_seconds"])

    if plan.get("narration_enabled") and (raw / "narration.wav").exists():
        looped_a = mix_narration_over_bed(
            raw / "narration.wav", looped_a, work / "audio_mixed.m4a",
            cfg["audio"].get("bed_gain", a["bed_gain_under_narration"]))

    out = dirs["pending_review"] / f"{slug}__{plan.get('scene_id','scene')}__{variant}.mp4"
    mux(looped_v, looped_a, out)
    print(f"[assemble] -> {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("--variant", default="3h", choices=list(HOURS))
    args = ap.parse_args()
    assemble(args.channel, args.variant)
