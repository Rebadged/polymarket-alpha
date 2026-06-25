"""Stage 1 — generation.

Picks the next (unused) scene for a channel and emits the generation jobs:
  1. still image   (z_image / recraft)        -> scene.png
  2. motion clip   (grok_video_v15 ...)        -> scene.mp4   (uses the still)
  3. music bed     (higgsfield audio / suno)   -> bed.wav

In backend=manifest mode this writes output/raw/<slug>/jobs.json for a Claude/MCP
session to fulfill. In backend=rest mode it generates directly. It also writes a
plan.json that assemble.py reads (which scene, which title, variation metadata).
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from . import state
from .config import load_channel, output_dirs
from .higgsfield_client import GenJob, HiggsfieldClient


def _fmt(text: str, identity: dict) -> str:
    """Inject {character}/{film_look} etc. from identity into a prompt template."""
    tokens = {"character": identity.get("character", ""),
              "film_look": identity.get("film_look", ""),
              "mood": identity.get("mood", "")}
    try:
        return text.format(**tokens)
    except (KeyError, IndexError):
        return text


def build_jobs(cfg: dict, scene: dict) -> list[GenJob]:
    g = cfg["generation"]
    identity = cfg["identity"]
    still_prompt = _fmt(scene["still_prompt"], identity) + " -- " + identity["negative"]
    motion_prompt = _fmt(scene["motion_prompt"], identity)
    jobs = [
        GenJob(
            kind="image",
            model=g["image_model"],
            prompt=still_prompt,
            out_name="scene.png",
            params={"aspect_ratio": g["aspect_ratio"]},
        ),
        GenJob(
            kind="video",
            model=g["video_model"],
            prompt=motion_prompt,
            out_name="scene.mp4",
            input_media="scene.png",            # resolved to the produced still
            params={"resolution": g["video_resolution"], "duration": g["clip_seconds"]},
        ),
    ]
    audio = cfg["audio"]
    if audio.get("bed_source") in ("higgsfield_native", "suno"):
        jobs.append(
            GenJob(
                kind="audio",
                model="higgsfield_audio" if audio["bed_source"] == "higgsfield_native" else "suno",
                prompt=audio["bed_prompt"],
                out_name="bed.wav",
                params={"loopable": True},
            )
        )
    # Narration lane: add a TTS job for the chosen script.
    narr = cfg.get("narration", {})
    if narr.get("enabled"):
        script = narr["script_pool"][0]
        jobs.append(
            GenJob(
                kind="audio",
                model="higgsfield_audio_tts",
                prompt=script["script"],
                out_name="narration.wav",
                params={"voice_id": narr.get("voice_id", ""), "wpm": narr.get("wpm", 110)},
            )
        )
    return jobs


def choose_title(cfg: dict, scene: dict, st: dict) -> str:
    human = scene["id"].replace("_", " ")
    templates = cfg["metadata"]["title_templates"]
    used = set(st.get("used_titles", []))
    random.shuffle(templates)
    for t in templates:
        title = t.format(scene_human=human)
        if title not in used:
            return title
    return templates[0].format(scene_human=human)


def main(slug: str) -> dict:
    cfg = load_channel(slug)
    dirs = output_dirs(cfg)
    st = state.load(slug)

    scene = state.next_scene(cfg, st)
    title = choose_title(cfg, scene, st)
    jobs = build_jobs(cfg, scene)

    client = HiggsfieldClient(cfg["generation"]["backend"], dirs["raw"])
    result = client.run(jobs)

    plan = {
        "slug": slug,
        "scene_id": scene["id"],
        "title": title,
        "raw_dir": str(dirs["raw"]),
        "backend": cfg["generation"]["backend"],
        "longform": cfg["longform"],
        "metadata": cfg["metadata"],
        "audio": cfg["audio"],
        "narration_enabled": cfg.get("narration", {}).get("enabled", False),
        "manifest": str(result) if isinstance(result, Path) else "generated",
    }
    (dirs["raw"] / "plan.json").write_text(json.dumps(plan, indent=2))

    state.record(slug, st, scene["id"], title)

    print(f"[generate] {slug}: scene={scene['id']} title={title!r}")
    if cfg["generation"]["backend"] == "manifest":
        print(f"[generate] manifest written -> {result}")
        print("[generate] NEXT: have a Claude Code/MCP session fulfill jobs.json, "
              "then run assemble.py")
    return plan


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    args = ap.parse_args()
    main(args.channel)
