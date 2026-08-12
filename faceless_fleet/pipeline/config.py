"""Load and merge global + per-channel YAML config."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent          # faceless_fleet/
CONFIG_DIR = ROOT / "config"
CHANNELS_DIR = CONFIG_DIR / "channels"


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_global() -> dict:
    with open(CONFIG_DIR / "global.yaml") as f:
        return yaml.safe_load(f)


def load_channel(slug: str) -> dict:
    """Return the channel config with global defaults merged underneath it."""
    path = CHANNELS_DIR / f"{slug}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No channel config: {path}")
    with open(path) as f:
        channel = yaml.safe_load(f)
    merged = _deep_merge(load_global(), channel)
    merged["_slug"] = slug
    return merged


def list_channels() -> list[str]:
    return sorted(p.stem for p in CHANNELS_DIR.glob("*.yaml"))


def output_dirs(cfg: dict) -> dict[str, Path]:
    """Resolve and create the per-channel stage folders."""
    slug = cfg["_slug"]
    root = ROOT / cfg["paths"]["output_root"]
    dirs = {
        "raw": root / "raw" / slug,
        "pending_review": root / "pending_review" / slug,
        "approved": root / "approved" / slug,
        "published": root / "published" / slug,
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


if __name__ == "__main__":
    import json
    import sys

    slug = sys.argv[1] if len(sys.argv) > 1 else "2am_without_her"
    print(json.dumps(load_channel(slug), indent=2, default=str))
