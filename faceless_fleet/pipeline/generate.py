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


class _SafeDict(dict):
    """format_map helper: leave unknown {tokens} (e.g. {dur}) untouched for later."""
    def __missing__(self, key):
        return "{" + key + "}"


def _tokens(cfg: dict, location: str = "") -> dict:
    identity = cfg["identity"]
    return {"character": identity.get("character", ""),
            "film_look": identity.get("film_look", ""),
            "mood": identity.get("mood", ""),
            "motion_principle": identity.get("motion_principle", ""),
            "location": location}


def _fmt(text: str, tokens: dict) -> str:
    """Inject {character}/{film_look}/{location} etc., leaving unknown tokens intact."""
    return text.format_map(_SafeDict(tokens))


def build_jobs(cfg: dict, scene: dict, tokens: dict, location_prompt: str = "") -> list[GenJob]:
    g = cfg["generation"]
    identity = cfg["identity"]
    still_prompt = _fmt(scene["still_prompt"], tokens)
    if location_prompt:                              # depict the rotated named place (descriptive form)
        still_prompt += f", set in {location_prompt}"
    still_prompt += " -- " + identity["negative"]
    motion_prompt = _fmt(scene["motion_prompt"], tokens)
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


def choose_title(cfg: dict, scene: dict, st: dict, tokens: dict) -> str:
    # {dur} is intentionally left for upload.py to fill per length variant.
    human = (tokens.get("location") or scene["id"].replace("_", " "))
    base = {**tokens, "keyword": scene.get("keyword", ""),
            "scene_human": scene["id"].replace("_", " ")}
    templates = list(cfg["metadata"]["title_templates"])
    used = set(st.get("used_titles", []))
    random.shuffle(templates)
    for t in templates:
        title = t.format_map(_SafeDict({**base, "scene_human": human}))
        if title not in used:
            return title
    return templates[0].format_map(_SafeDict({**base, "scene_human": human}))


def main(slug: str) -> dict:
    cfg = load_channel(slug)
    dirs = output_dirs(cfg)
    st = state.load(slug)

    scene = state.next_scene(cfg, st)
    location = state.next_location(cfg, st)          # {title, prompt} or ''
    loc_title = location["title"] if isinstance(location, dict) else ""
    loc_prompt = location["prompt"] if isinstance(location, dict) else ""
    tokens = _tokens(cfg, loc_title)                 # short form -> titles
    title = choose_title(cfg, scene, st, tokens)
    jobs = build_jobs(cfg, scene, tokens, loc_prompt)  # descriptive form -> image

    client = HiggsfieldClient(cfg["generation"]["backend"], dirs["raw"])
    result = client.run(jobs)

    plan = {
        "slug": slug,
        "scene_id": scene["id"],
        "weather": scene.get("weather", ""),
        "audio_hint": scene.get("audio_hint", ""),   # which Suno bed to make/use
        "location": loc_title,
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

    state.record(slug, st, scene["id"], title, loc_title)

    print(f"[generate] {slug}: scene={scene['id']} location={loc_title!r} title={title!r}")
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
