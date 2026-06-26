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
import hashlib
import json
import random
import subprocess
from pathlib import Path

from .config import ROOT, load_channel, output_dirs

HOURS = {"1h": 3600, "3h": 10800, "8h": 28800}


def _run(cmd: list[str]) -> None:
    print("[ffmpeg]", " ".join(str(c) for c in cmd[:6]), "...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def _probe_duration(path: Path) -> float:
    for entries in ("format=duration", "stream=duration"):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", entries,
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True).stdout.strip().splitlines()
        for line in out:
            try:
                return float(line)
            except ValueError:
                continue
    raise ValueError(f"could not probe duration of {path}")


def make_seamless_video(clip: Path, out: Path, xfade: float, fps: int) -> Path:
    """Crossfade the clip's end-wrap into its start so a stream_loop has NO visible
    seam. Technique: with D=duration, X=xfade, take tail=clip[X:D] and head=clip[0:X]
    and xfade(tail, head, offset=D-2X). The result starts AND ends on the same frame
    (clip @ time X), so looping it is seamless; the true end->start wrap is hidden in
    the mid-clip crossfade. Output length = D - X."""
    d = _probe_duration(clip)
    if xfade <= 0 or d <= 2 * xfade + 0.1:   # too short to wrap-fade; leave as-is
        _run(["ffmpeg", "-y", "-i", str(clip), "-c", "copy", str(out)])
        return out
    fc = (f"[0:v]trim=0:{xfade},setpts=PTS-STARTPTS[head];"
          f"[0:v]trim={xfade}:{d},setpts=PTS-STARTPTS[tail];"
          f"[tail][head]xfade=transition=fade:duration={xfade}:offset={d - 2*xfade}[v]")
    _run(["ffmpeg", "-y", "-i", str(clip), "-filter_complex", fc, "-map", "[v]",
          "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out)])
    return out


def build_sfx_bed(layers: list[dict], library: dict, sfx_dir: Path, out: Path,
                  unit_seconds: int = 90) -> Path:
    """Mix reusable SFX elements (rain/thunder/fire/wind) into one bed at per-scene
    levels. Each layer = {el, gain}; el maps to a file via `library`. Every element
    is looped to a common unit length, gain-staged, mixed, and limited to avoid
    clipping. The result (a ~90s wav) feeds the normal seamless-loop audio path, so
    you grab ~5 element files ONCE and the pipeline builds every video's bed.

    sleep-safe gains live in the scene config (e.g. thunder 0.5, fire 0.25)."""
    def _resolve(name: str):
        p = sfx_dir / name
        if p.exists():
            return p
        stem = Path(name).stem                       # tolerate .mp3 vs .wav etc.
        for ext in (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"):
            c = sfx_dir / (stem + ext)
            if c.exists():
                return c
        return None

    present = [(l, _resolve(library.get(l["el"], ""))) for l in layers]
    present = [(l, f) for l, f in present if f]
    if not present:
        raise FileNotFoundError(
            f"No SFX element files found in {sfx_dir} for layers {[l['el'] for l in layers]}. "
            f"Download them (see LAUNCH_PLAN.md) or drop a ready bed.wav in the raw dir.")
    inputs, filt = [], []
    for i, (layer, f) in enumerate(present):
        inputs += ["-stream_loop", "-1", "-i", str(f)]
        filt.append(f"[{i}:a]volume={layer.get('gain', 1.0)}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(present)))
    fc = (";".join(filt) +
          f";{mix}amix=inputs={len(present)}:normalize=0:duration=shortest,"
          f"alimiter=limit=0.95[out]")
    _run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[out]",
          "-t", str(unit_seconds), "-c:a", "pcm_s16le", str(out)])
    return out


def make_seamless_audio(bed: Path, out: Path, xfade: float, lufs: float) -> Path:
    """Seamless audio loop unit + loudness normalization. Wraps the bed's end into
    its start so a stream_loop has no audible seam: take tail=bed[X:D] and head=
    bed[0:X], acrossfade(tail, head) -> unit that starts AND ends on the sample @
    time X. loudnorm pins output loudness so no volume spike wakes a sleeper.

    NOTE: acrossfade starves if both inputs are atrim branches of the same source,
    so head/tail are extracted to temp WAVs first (crossfading two files is robust)."""
    d = _probe_duration(bed)
    norm = f"loudnorm=I={lufs}:TP=-1.5:LRA=11"
    if xfade <= 0 or d <= 2 * xfade + 0.1:
        _run(["ffmpeg", "-y", "-i", str(bed), "-af", norm,
              "-c:a", "aac", "-b:a", "192k", str(out)])
        return out
    head = out.with_name("_ahead.wav")
    tail = out.with_name("_atail.wav")
    _run(["ffmpeg", "-y", "-i", str(bed), "-t", str(xfade), "-c:a", "pcm_s16le", str(head)])
    _run(["ffmpeg", "-y", "-ss", str(xfade), "-i", str(bed), "-c:a", "pcm_s16le", str(tail)])
    _run(["ffmpeg", "-y", "-i", str(tail), "-i", str(head),
          "-filter_complex", f"[0:a][1:a]acrossfade=d={xfade}:c1=tri:c2=tri[ax];[ax]{norm}[a]",
          "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(out)])
    return out


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


def _resolve_seconds(slug: str, cfg: dict, variant: str) -> int:
    """Fixed HOURS variant, or an ORGANIC length from config (target_seconds +/- jitter).
    Jitter is seeded per-slug so a given channel's length is stable across re-runs but
    never an exactly-round number (avoids the 'suspiciously exact 3:00:00' tell)."""
    if variant in HOURS:
        return HOURS[variant]
    lf = cfg.get("longform", {})
    base = int(lf.get("target_seconds", HOURS["3h"]))
    jitter = int(lf.get("jitter_seconds", 0))
    if jitter:
        rng = random.Random(hashlib.sha256(f"{slug}:{variant}".encode()).hexdigest())
        base += rng.randint(-jitter, jitter)
    return base


def assemble(slug: str, variant: str = "3h") -> Path:
    cfg = load_channel(slug)
    dirs = output_dirs(cfg)
    raw = dirs["raw"]
    plan = json.loads((raw / "plan.json").read_text(encoding="utf-8-sig")) if (raw / "plan.json").exists() else {}

    seconds = _resolve_seconds(slug, cfg, variant)
    a = cfg["assembly"]
    work = raw / "_work"
    work.mkdir(exist_ok=True)

    seamless = cfg.get("longform", {}).get("seamless_loop", False)
    lufs = cfg.get("audio", {}).get("loudness_lufs", a.get("default_loudness_lufs", -14))

    # --- video base: prefer the motion clip, else Ken Burns the still ---
    if (raw / "scene.mp4").exists():
        base_clip = raw / "scene.mp4"
    elif (raw / "scene.png").exists():
        base_clip = kenburns_from_still(raw / "scene.png", work / "kenburns.mp4", cfg, 20)
    else:
        raise FileNotFoundError(
            f"No scene.mp4 or scene.png in {raw}. Fulfill the generation manifest first."
        )
    # Seamless loop unit: crossfade the wrap so the seam is invisible across hours.
    if seamless:
        base_clip = make_seamless_video(
            base_clip, work / "video_unit.mp4", a["loop_video_xfade_seconds"], a["fps"])
    looped_v = loop_to_length(base_clip, work / "video_long.mp4", seconds)

    # --- audio base (seamless unit + loudness-normalized) ---
    # Prefer building the bed from reusable SFX elements at per-scene levels; fall
    # back to a ready-made bed.wav dropped in the raw dir.
    bed = raw / "bed.wav"
    audio_cfg = cfg.get("audio", {})
    scene = next((s for s in cfg.get("scene_pool", []) if s["id"] == plan.get("scene_id")), {})
    layers = scene.get("audio_layers")
    if layers and audio_cfg.get("sfx_library"):
        sfx_dir = ROOT / audio_cfg.get("sfx_dir", "assets/sfx")
        try:
            bed = build_sfx_bed(layers, audio_cfg["sfx_library"], sfx_dir, work / "bed_sfx.wav")
        except FileNotFoundError as e:
            if not bed.exists():
                raise
            print(f"[assemble] SFX layers unavailable ({e}); using bed.wav")
    if not bed.exists():
        raise FileNotFoundError(f"No SFX elements and no bed.wav in {raw}.")
    audio_unit = make_seamless_audio(
        bed, work / "audio_unit.m4a",
        a["loop_audio_xfade_seconds"] if seamless else 0.0, lufs)
    looped_a = loop_to_length(audio_unit, work / "audio_long.m4a", seconds)

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
