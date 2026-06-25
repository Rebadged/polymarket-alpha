"""Tiny per-channel state store so we never repeat a scene/track/title
(the core of YouTube's per-video variation requirement)."""
from __future__ import annotations

import json
from pathlib import Path

from .config import ROOT


def _state_path(slug: str) -> Path:
    p = ROOT / "output" / "state"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{slug}.json"


def load(slug: str) -> dict:
    p = _state_path(slug)
    if p.exists():
        return json.loads(p.read_text())
    return {"used_scenes": [], "used_titles": [], "history": []}


def save(slug: str, state: dict) -> None:
    _state_path(slug).write_text(json.dumps(state, indent=2))


def next_scene(cfg: dict, state: dict) -> dict:
    """Pick the least-recently-used scene from the pool."""
    pool = cfg["scene_pool"]
    used = state.get("used_scenes", [])
    # Prefer a scene never used; otherwise the one used longest ago.
    unused = [s for s in pool if s["id"] not in used]
    if unused:
        return unused[0]
    # all used at least once -> rotate by oldest usage
    order = {sid: i for i, sid in enumerate(used)}
    return min(pool, key=lambda s: order.get(s["id"], -1))


def _loc_key(entry) -> str:
    """A location pool entry is either a string or {title, prompt}. Dedup by title."""
    return entry["title"] if isinstance(entry, dict) else entry


def next_location(cfg: dict, state: dict):
    """Rotate named locations (a different place each video) for per-video variation
    + SEO seasoning. Returns a {title, prompt} dict (or '' if no pool). Per the
    geography research: location is variation/search seasoning, NOT an RPM lever."""
    pool = cfg.get("location_pool") or []
    if not pool:
        return ""
    used = state.get("used_locations", [])
    unused = [e for e in pool if _loc_key(e) not in used]
    if unused:
        chosen = unused[0]
    else:
        order = {k: i for i, k in enumerate(used)}
        chosen = min(pool, key=lambda e: order.get(_loc_key(e), -1))
    return chosen if isinstance(chosen, dict) else {"title": chosen, "prompt": chosen}


def record(slug: str, state: dict, scene_id: str, title: str, location: str = "") -> None:
    state.setdefault("used_scenes", []).append(scene_id)
    state.setdefault("used_titles", []).append(title)
    if location:
        state.setdefault("used_locations", []).append(location)
        state["used_locations"] = state["used_locations"][-50:]
    state.setdefault("history", []).append(
        {"scene": scene_id, "location": location, "title": title})
    # keep the rolling window from growing unbounded
    state["used_scenes"] = state["used_scenes"][-50:]
    state["used_titles"] = state["used_titles"][-50:]
    save(slug, state)
