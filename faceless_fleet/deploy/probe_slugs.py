#!/usr/bin/env python3
"""Discover the Higgsfield Cloud-API model slugs + prove the pipeline, in one run.

Runs ONLY where there's real internet (your VPS) — Claude sandboxes are denied egress
to platform.higgsfield.ai. It tries candidate slugs until one authenticates, so you
don't hand-guess. Cost is bounded to ~one real clip:
  * image candidates are cheap (~0.1 cr); wrong slugs 404 for free. Stops at first hit.
  * video candidates are ~7.5 cr each, so it STOPS at the first that works (typically 1).

On success it prints the two working slugs and (with --write) saves them into
config/global.yaml so `restock-run` works immediately. The generated still+clip URLs
are recorded to restock/<slug>.json and the clip downloaded to assets/clips/<slug>/.

  export HIGGSFIELD_API_KEY=...           # or HF_KEY
  ./venv/bin/python faceless_fleet/deploy/probe_slugs.py --write
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# make `faceless_fleet` importable when run as a plain script from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from faceless_fleet.pipeline import rest, restock          # noqa: E402
from faceless_fleet.pipeline.config import ROOT             # noqa: E402

IMAGE_CANDIDATES = [
    "higgsfield/soul/text-to-image",
    "higgsfield/soul-id/text-to-image",
    "higgsfield/soul/image",
    "bytedance/seedream/v4/text-to-image",   # proven-good fallback (different look)
]
VIDEO_CANDIDATES = [
    "higgsfield/kling-3-turbo/image-to-video",
    "kwaivgi/kling-v3-turbo/image-to-video",
    "kling/v3-turbo/image-to-video",
    "higgsfield/kling/image-to-video",
]

TEST_PROMPT = "a cozy snowy log cabin at night, warm glowing windows, painterly"
TEST_MOTION = "thick snow falling gently, warm window light flickering, locked camera"


def _probe_image(hf):
    for app in IMAGE_CANDIDATES:
        try:
            r = hf.subscribe(app, arguments={"prompt": TEST_PROMPT, "aspect_ratio": "16:9"})
            url = rest._extract_url(r, "images[0].url", "image.url", "url")
            print(f"  IMAGE  ✓ {app}")
            return app, url
        except Exception as e:
            print(f"  IMAGE  ✗ {app}  ({str(e)[:70]})")
    return None, None


def _probe_video(hf, image_url):
    for app in VIDEO_CANDIDATES:
        try:
            r = hf.subscribe(app, arguments={
                "prompt": TEST_MOTION, "image_url": image_url,
                "duration": 10, "aspect_ratio": "16:9"})
            url = rest._extract_url(r, "video.url", "videos[0].url", "url")
            print(f"  VIDEO  ✓ {app}")
            return app, url
        except Exception as e:
            print(f"  VIDEO  ✗ {app}  ({str(e)[:70]})")
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="save the discovered slugs into config/global.yaml")
    ap.add_argument("--slug", default="rain_cabin", help="channel to file the test clip under")
    args = ap.parse_args()

    rest._ensure_key()
    import higgsfield_client as hf

    print("[probe] discovering image slug…")
    img_app, img_url = _probe_image(hf)
    if not img_app:
        print("\n[probe] NO image slug worked. If all showed 401/403 the key/header is wrong; "
              "if 404 the candidate list needs the real slug from cloud.higgsfield.ai.")
        return 1

    print("[probe] discovering image-to-video slug (stops at first hit)…")
    vid_app, vid_url = _probe_video(hf, img_url)
    if not vid_app:
        print(f"\n[probe] image slug works ({img_app}) but no video slug did. "
              "Auth is fine; just need the real image-to-video slug.")
        return 1

    # record + download the proof clip
    clip_name = "probe_test__first.mp4"
    restock.record(args.slug, clip_name, vid_url, img_url)
    dest = restock._clips_dir(args.slug) / clip_name
    ok = restock._download(vid_url, dest)

    print("\n========== RESULT ==========")
    print(f"  rest_image_model: {img_app}")
    print(f"  rest_video_model: {vid_app}")
    print(f"  test clip: {'downloaded -> ' + str(dest) if ok else 'generated (URL recorded; download failed)'}")
    print("============================")

    if args.write:
        cfg_path = ROOT / "config" / "global.yaml"
        text = cfg_path.read_text(encoding="utf-8")
        for key, val in (("rest_image_model", img_app), ("rest_video_model", vid_app)):
            import re
            text = re.sub(rf"(?m)^(\s*{key}:).*$", rf"\1 \"{val}\"", text)
        cfg_path.write_text(text, encoding="utf-8")
        print(f"[probe] wrote slugs into {cfg_path}")
        print("[probe] tell the assistant these two slugs so it commits them to the repo too.")
    else:
        print("[probe] re-run with --write to save these into config/global.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
