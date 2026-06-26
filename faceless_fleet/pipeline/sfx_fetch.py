"""Auto-fetch ambient SFX from Freesound (official API, CC0 = no attribution).

This replaces the manual "browse Pixabay, download, rename" step. It searches
Freesound for Creative-Commons-0 sounds matching each element, prefers LONGER
high-rated clips (longer = fewer loop repeats = better audio), and saves them
into assets/sfx/ with the exact canonical names the pipeline expects.

Setup (one time, free):
  1. Make a Freesound account -> https://freesound.org
  2. Apply for an API key -> https://freesound.org/apiv2/apply/
  3. Put it in an env var:  FREESOUND_API_KEY=...

Usage:
  python -m faceless_fleet.pipeline.run fetch-sfx            # all 5 elements
  python -m faceless_fleet.pipeline.run fetch-sfx --only fireplace --count 3

Why Freesound: it has an official search+download API built exactly for this,
and a CC0 filter so everything is license-clean for monetized YouTube. (Pixabay
has no sound-effects API; scraping it would be fragile + against ToS.)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

from .config import ROOT

API = "https://freesound.org/apiv2"

# element -> (search query, [min_seconds, max_seconds]). Longer = better loops.
DEFAULT_SOURCES = {
    "rain_heavy":      ("heavy rain", (120, 1200)),
    "rain_light":      ("light gentle rain", (120, 1200)),
    "thunder_distant": ("distant rolling thunder rumble", (90, 1200)),
    "fireplace":       ("fireplace crackling fire", (120, 1800)),
    "wind_winter":     ("cold winter wind", (120, 1800)),
    # campfire / camping focal points
    "crickets":        ("night crickets ambience", (120, 1800)),
    "lake_water":      ("gentle lake water lapping shore", (120, 1800)),
    "rain_on_tent":    ("rain on tent", (60, 1200)),
}


def _key() -> str:
    k = os.environ.get("FREESOUND_API_KEY")
    if not k:
        sys.exit("Missing FREESOUND_API_KEY. Get one free at "
                 "https://freesound.org/apiv2/apply/ and set the env var.")
    return k


def _search(query: str, dur: tuple[int, int], token: str) -> list[dict]:
    r = requests.get(f"{API}/search/text/", params={
        "query": query,
        "filter": f'license:"Creative Commons 0" duration:[{dur[0]} TO {dur[1]}]',
        "fields": "id,name,duration,license,previews,avg_rating,num_downloads",
        "sort": "rating_desc",
        "page_size": 15,
    }, headers={"Authorization": f"Token {token}"}, timeout=30)
    r.raise_for_status()
    return r.json().get("results", [])


def _download(url: str, dest: Path, token: str) -> None:
    r = requests.get(url, headers={"Authorization": f"Token {token}"}, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)


def fetch(only: str | None = None, count: int = 1, out_dir: Path | None = None) -> None:
    token = _key()
    out_dir = out_dir or (ROOT / "assets" / "sfx")
    out_dir.mkdir(parents=True, exist_ok=True)
    items = DEFAULT_SOURCES.items() if not only else [(only, DEFAULT_SOURCES[only])]

    for name, (query, dur) in items:
        results = _search(query, dur, token)
        if not results:
            print(f"[fetch-sfx] no CC0 results for {name!r} ({query!r}); widen the search.")
            continue
        picked = results[:count]
        for i, snd in enumerate(picked):
            # canonical name for count=1, else numbered variants (fireplace_1, ...)
            fname = f"{name}.mp3" if count == 1 else f"{name}_{i+1}.mp3"
            url = snd["previews"].get("preview-hq-mp3") or snd["previews"].get("preview-lq-mp3")
            _download(url, out_dir / fname, token)
            print(f"[fetch-sfx] {fname}  <- '{snd['name']}' "
                  f"({snd['duration']:.0f}s, ★{snd.get('avg_rating',0):.1f}) "
                  f"freesound#{snd['id']}")
    print(f"[fetch-sfx] done -> {out_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(DEFAULT_SOURCES))
    ap.add_argument("--count", type=int, default=1)
    args = ap.parse_args()
    fetch(args.only, args.count)
