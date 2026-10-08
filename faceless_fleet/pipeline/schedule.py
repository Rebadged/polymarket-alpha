"""Jittered scheduling — the #1 anti-spam control.

Produces a randomized ISO-8601 publishAt so videos drip out at human-plausible
times instead of all firing at the same minute. Mirrors the deterministic-jitter
idea Claude Code's own scheduler uses to avoid thundering-herd posting.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import random


def _seeded_rng(seed_str: str) -> random.Random:
    h = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    return random.Random(h)


def next_publish_at(cfg: dict, seed: str, now: dt.datetime | None = None) -> str:
    """ISO-8601 UTC publish time at the channel's base hour +/- jitter, at least
    `min_hours_between_uploads` in the future. `seed` (e.g. video filename) makes
    the jitter deterministic per-video so re-runs don't reshuffle the calendar."""
    up = cfg["upload"]
    now = now or dt.datetime.now(dt.timezone.utc)
    rng = _seeded_rng(seed)

    min_gap = dt.timedelta(hours=up.get("min_hours_between_uploads", 20))
    target_day = (now + min_gap).date()

    base_hour = up.get("base_publish_hour_utc", 2)
    jitter = up.get("jitter_minutes", 50)
    offset = rng.randint(-jitter, jitter)

    when = dt.datetime(target_day.year, target_day.month, target_day.day,
                       base_hour, 0, tzinfo=dt.timezone.utc) + dt.timedelta(minutes=offset)
    if when < now + min_gap:
        when += dt.timedelta(days=1)
    return when.replace(microsecond=0).isoformat()


if __name__ == "__main__":
    import sys

    from .config import load_channel
    slug = sys.argv[1] if len(sys.argv) > 1 else "2am_without_her"
    cfg = load_channel(slug)
    for name in ["a.mp4", "b.mp4", "c.mp4"]:
        print(name, "->", next_publish_at(cfg, name))
