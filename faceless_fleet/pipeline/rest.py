"""Unattended restock via the Higgsfield Cloud API (no agent / no Claude session).

This is the alternative to the weekly scheduled-session path (restock.py). With a
`HIGGSFIELD_API_KEY` on the box it plans -> generates the still -> animates -> downloads
straight into the clip library, so a single VPS cron line does the whole restock.

Set `generation.backend: rest` to make the pipeline use this. It is intentionally driven
by config so the exact Cloud-API model slugs / argument names live in YAML, not code
(the Cloud API uses fal-style slugs like `bytedance/seedream/v4/text-to-image`, which
differ from the MCP names `soul_2` / `kling3_0_turbo`). Confirm the slugs once against
the live key, drop them into config/global.yaml under generation.rest_*, and this runs.

  python -m faceless_fleet.pipeline.run restock-run rain_cabin --budget 56

The SDK (`pip install higgsfield-client`) handles base URL, auth and polling. It reads
the key from HF_KEY/HF_API_KEY; we bridge our canonical HIGGSFIELD_API_KEY to that.
"""
from __future__ import annotations

import argparse
import os

from . import batch_plan, restock
from .config import ROOT, load_channel


def _ensure_key() -> str:
    """Accept our canonical name and bridge it to what the SDK expects."""
    key = os.environ.get("HIGGSFIELD_API_KEY") or os.environ.get("HF_API_KEY") or os.environ.get("HF_KEY")
    if not key:
        raise RuntimeError(
            "No Higgsfield API key. Set HIGGSFIELD_API_KEY in the environment "
            "(VPS .env or the web environment settings)."
        )
    os.environ.setdefault("HF_KEY", key)
    os.environ.setdefault("HF_API_KEY", key)
    return key


def _extract_url(result: dict, *candidates: str) -> str:
    """Pull a media URL out of an SDK result across the shapes it may return
    (result['images'][0]['url'], result['video']['url'], result['url'], …)."""
    for c in candidates:
        node = result
        ok = True
        for part in c.split("."):
            if part.endswith("[0]"):
                part = part[:-3]
                node = node.get(part) if isinstance(node, dict) else None
                node = node[0] if isinstance(node, list) and node else None
            else:
                node = node.get(part) if isinstance(node, dict) else None
            if node is None:
                ok = False
                break
        if ok and isinstance(node, str):
            return node
    raise KeyError(f"no media URL in result; looked for {candidates}; got keys={list(result)}")


def generate_clip(slug: str, item: dict, cfg: dict) -> dict:
    """Generate one clip (still -> video) and download it into the library.
    Returns {clip_name, video_url, image_url}. Raises on failure."""
    import higgsfield_client as hf  # imported lazily so the rest of the CLI needs no SDK

    gen = cfg["generation"]
    img_model = gen.get("rest_image_model") or gen["image_model"]
    vid_model = gen.get("rest_video_model") or gen["video_model"]

    still = hf.subscribe(img_model, arguments={
        "prompt": item["still_prompt"],
        "aspect_ratio": item.get("aspect_ratio", "16:9"),
        "resolution": gen.get("rest_image_resolution", "2K"),
        "camera_fixed": True,
    })
    image_url = _extract_url(still, "images[0].url", "image.url", "url")

    clip = hf.subscribe(vid_model, arguments={
        "prompt": item["motion_prompt"],
        "image_url": image_url,
        "duration": item.get("duration", gen.get("clip_seconds", 10)),
        "aspect_ratio": item.get("aspect_ratio", "16:9"),
    })
    video_url = _extract_url(clip, "video.url", "videos[0].url", "url")

    restock.record(slug, item["clip_name"], video_url, image_url)   # log URL (manifest)
    dest = restock._clips_dir(slug) / item["clip_name"]
    if not restock._download(video_url, dest):
        raise RuntimeError(f"download failed for {item['clip_name']}")
    return {"clip_name": item["clip_name"], "video_url": video_url, "image_url": image_url}


def fulfill(slug: str, budget_credits: float = 56) -> dict:
    """Plan a budgeted batch for one channel and generate it end to end."""
    _ensure_key()
    cfg = load_channel(slug)
    per = cfg["generation"].get("est_credits_per_clip", 8)
    manifest = batch_plan.plan(slug, budget_credits)
    made, spent = [], 0.0
    for item in manifest["items"]:
        if spent + per > budget_credits:
            break
        try:
            made.append(generate_clip(slug, item, cfg))
            spent += per
            print(f"[restock-run] {slug}: + {item['clip_name']} (~{spent:.0f}/{budget_credits} cr)")
        except Exception as e:
            print(f"[restock-run] {slug}: FAILED {item['clip_name']}: {e}")
    print(f"[restock-run] {slug}: generated {len(made)} clip(s), ~{spent:.0f} credits")
    return {"slug": slug, "made": made, "est_credits": spent}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("--budget", type=float, default=56)
    a = ap.parse_args()
    fulfill(a.channel, a.budget)
