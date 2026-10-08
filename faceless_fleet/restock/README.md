# restock/ — the clip transport manifests

One small JSON per channel (`<slug>.json`), written by the weekly Claude scheduled
session and read by the VPS. Each entry is just a generated clip's **download URL** —
no video bytes ever live here, so it's safe and cheap to commit.

```json
[
  { "clip_name": "snowy_cabin_exterior__canadian_rockies_cabin.mp4",
    "video_url": "https://…/clip.mp4", "image_url": "https://…/still.jpg",
    "fetched": false }
]
```

- The scheduled session appends entries via `restock-record` after each generation.
- The VPS `weekly` run calls `restock-fetch` (automatically) to download any entry whose
  clip isn't in `assets/clips/<slug>/` yet, then flips `fetched: true`.

`fetched` is just bookkeeping — `restock-fetch` is idempotent and re-pulls anything
missing from the library regardless. See deploy/RESTOCK_SCHEDULE.md.
