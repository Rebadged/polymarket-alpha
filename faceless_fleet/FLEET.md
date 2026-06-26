# The Fleet — focal-point taxonomy

The vibe is the product. The **audio is the star**, the **visual is the hook**.

## The model

```
  FOCAL POINT (= channel)   ×   WEATHER/SEASON   ->   AUDIO + PLAYLIST
  cabin, campfire, tent,        snow, rain,           layered SFX, grouped
  window, ...                   storm, clear          into binge playlists
```

- **Focal point = one channel.** Sharp topic identity = better algorithm signal.
- **Weather × season = per-video variation** (the inauthentic-content safeguard)
  and it **drives the audio mix**:
  - cabin + snow + fire  → fire crackle + light wind
  - cabin + rain + fire  → fire crackle + rain
  - tent + rain          → rain on canvas
  - campfire + light rain → fire + the "ptsss" sizzle of drops on flame
- **Playlists by experience** (Snowy Cabin Nights, Rainy Cabin Nights, …) +
  autoplay = the whole night loops on your channel = stacked watch-hours.
- **Meditation is its own lane** (narrated) — not in the focal-point group.

## Channels (focal points)

| # | Channel | Focal point | Status |
|---|---------|-------------|--------|
| 1 | **Cabin Comforts** | cabin | LIVE — building |
| 2 | (e.g. *Campfire Nights*) | campfire | template-ready |
| 3 | (e.g. *Tent & Rain* / camping) | tent | template-ready |
| — | meditation (narrated) | — | separate lane, later |

Each new channel = copy `rain_cabin.yaml`, swap `focal_point` + the scene prompts
(same engine: scenes = focal×weather, `audio_layers`, `weather_map` playlists).

## Token economy (keep it lean)

- **Clips are reusable + looped**, so each channel needs only a small periodic
  batch, not per-video generation. Short clips (5–15s) loop seamlessly.
- **Split the monthly credit budget evenly** across active channels; each just
  needs ~5–15 fresh clips per stock-up (≈40–110 credits/channel/batch).
- **Reuse before regenerating**: `deploy/stock_clips.py` seeds the library from
  clips already made — zero new tokens. Generate new ones only to add variety.

## Stocking the clip library

- **Now (free):** `python faceless_fleet/deploy/stock_clips.py rain_cabin` pulls
  this session's 5 approved clips (one per scene) into the library → enough to launch.
- **Later (cheap):** add a few clips per scene/location for more visual variety,
  or per new focal-point channel.
