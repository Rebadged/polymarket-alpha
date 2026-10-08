"""Stock the clip library from clips we ALREADY generated (no new tokens).

Downloads the session's approved Cabin Comforts clips into
assets/clips/<channel>/<scene_id>__<name>.mp4 so the `auto` loop can start.
Cross-platform (Windows PC or VPS) — both have open egress to the CDN.

Run from the repo root:
    python faceless_fleet/deploy/stock_clips.py rain_cabin
"""
import sys
from pathlib import Path

import requests

CDN = "https://d8j0ntlcm91z4.cloudfront.net/user_3FdTKdOtC6CmqWtVhwJcIt6v5Ik/"

# scene_id__name  ->  CDN filename. Reuses this session's approved clips.
CLIPS = {
    "rain_cabin": {
        "snowy_cabin_exterior__rockies01": "hf_20260625_193636_1aeec6e9-d34b-467d-8757-e88923ed636b.mp4",
        "cabin_window_glow_rain__pnw01":   "hf_20260625_194630_87a59708-fc4d-43e5-b6c0-16c287bf6b47.mp4",
        "frozen_lake_cabin__norway01":     "hf_20260625_194633_cc6ea07d-6b57-4516-824b-1dacfb59cc8a.mp4",
        "porch_storm__highlands01":        "hf_20260625_194636_59808cff-3afb-4728-932f-d16972128914.mp4",
        "fireplace_closeup__cabin01":      "hf_20260625_194639_28bd4366-e102-4dc5-a504-a1bc80f2a1a2.mp4",
    },
}


def main(channel: str) -> None:
    if channel not in CLIPS:
        sys.exit(f"No staged clips for {channel}. Known: {list(CLIPS)}")
    root = Path(__file__).resolve().parent.parent          # faceless_fleet/
    out = root / "assets" / "clips" / channel
    out.mkdir(parents=True, exist_ok=True)
    for name, fname in CLIPS[channel].items():
        dest = out / f"{name}.mp4"
        print(f"[stock] {dest.name}  <- {fname}")
        r = requests.get(CDN + fname, timeout=180)
        r.raise_for_status()
        dest.write_bytes(r.content)
    print(f"[stock] {len(CLIPS[channel])} clips -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "rain_cabin")
