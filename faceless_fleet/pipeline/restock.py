"""Restock bridge — carry generated clips from a Claude scheduled session to the VPS.

The restock step is the one part that needs Higgsfield (an agent), so it runs in a
weekly Claude *scheduled session*. That session lives in a fresh container that can't
reach the VPS's clip folder, and the sandbox can't download Higgsfield's CDN anyway.
So we split it across the git remote:

  Sunday, in the Claude scheduled session (deploy/RESTOCK_SCHEDULE.md):
    batch-plan -> generate via Higgsfield -> `restock-record <slug> <clip> --video-url …`
    -> commit + push the tiny `restock/<slug>.json` manifest (URLs only, no bytes).

  Sunday, slightly later, on the VPS (folded into `weekly`):
    git pull -> fetch_pending(slug) downloads each URL into assets/clips/<slug>/<clip>
    -> publish the week.

The manifest is committed (small, text); the video bytes travel over plain HTTPS to the
VPS, which has normal internet. fetch_pending is idempotent: a clip already in the
library (or already marked fetched) is skipped, so re-runs are safe.

  python -m faceless_fleet.pipeline.run restock-record rain_cabin snowy__x.mp4 --video-url https://…
  python -m faceless_fleet.pipeline.run restock-fetch  rain_cabin
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

from .config import ROOT, load_channel

RESTOCK_DIR = ROOT / "restock"          # tracked in git (URLs only — see .gitignore note)


def _manifest_path(slug: str) -> Path:
    return RESTOCK_DIR / f"{slug}.json"


def _load(slug: str) -> list[dict]:
    p = _manifest_path(slug)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8-sig") or "[]")


def _save(slug: str, entries: list[dict]) -> None:
    RESTOCK_DIR.mkdir(parents=True, exist_ok=True)
    _manifest_path(slug).write_text(json.dumps(entries, indent=2), encoding="utf-8")


def record(slug: str, clip_name: str, video_url: str, image_url: str | None = None) -> None:
    """Append (or update) one generated clip's download URL. Called by the scheduled
    session after generate_video, once per manifest item."""
    if not clip_name.endswith(".mp4"):
        clip_name += ".mp4"
    entries = _load(slug)
    for e in entries:
        if e["clip_name"] == clip_name:
            e.update(video_url=video_url, image_url=image_url, fetched=False)
            break
    else:
        entries.append({
            "clip_name": clip_name, "video_url": video_url,
            "image_url": image_url, "fetched": False,
        })
    _save(slug, entries)
    print(f"[restock-record] {slug}: {clip_name} <- {video_url[:60]}…")


def _clips_dir(slug: str) -> Path:
    cfg = load_channel(slug)
    return ROOT / cfg.get("auto", {}).get("clips_dir", "assets/clips") / slug


def _download(url: str, dest: Path, tries: int = 4) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                while chunk := r.read(1 << 16):
                    f.write(chunk)
            if tmp.stat().st_size < 1024:                  # guard against an error page
                raise OSError(f"suspiciously small download ({tmp.stat().st_size}B)")
            tmp.replace(dest)
            return True
        except Exception as e:
            wait = 2 ** i
            print(f"[restock-fetch] {dest.name} try {i+1}/{tries} failed: {e}; retry in {wait}s")
            tmp.unlink(missing_ok=True)
            if i < tries - 1:
                time.sleep(wait)
    return False


def fetch_pending(slug: str) -> int:
    """Download every recorded clip not yet in the library. Idempotent. Returns #fetched.
    Runs on the VPS (normal internet) — folded into `weekly` so it's automatic."""
    entries = _load(slug)
    if not entries:
        return 0
    clips = _clips_dir(slug)
    got = 0
    for e in entries:
        dest = clips / e["clip_name"]
        if dest.exists():
            e["fetched"] = True
            continue
        if e.get("fetched") and not dest.exists():
            e["fetched"] = False                           # library was cleared — re-pull
        if not e.get("video_url"):
            continue
        if _download(e["video_url"], dest):
            e["fetched"] = True
            got += 1
            print(f"[restock-fetch] {slug}: + {e['clip_name']}")
        else:
            print(f"[restock-fetch] {slug}: FAILED {e['clip_name']} (URL may have expired)")
    _save(slug, entries)
    if got:
        print(f"[restock-fetch] {slug}: pulled {got} new clip(s) into {clips}")
    return got


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("record")
    pr.add_argument("slug"); pr.add_argument("clip_name")
    pr.add_argument("--video-url", required=True); pr.add_argument("--image-url")
    pf = sub.add_parser("fetch")
    pf.add_argument("slug")
    a = ap.parse_args()
    if a.cmd == "record":
        record(a.slug, a.clip_name, a.video_url, a.image_url)
    else:
        fetch_pending(a.slug)
