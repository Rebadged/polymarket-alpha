# Cabin Comforts — Launch Slate (first 5 videos)

Five distinct scenes = genuine per-video variation (the inauthentic-content guard).
Each clip already exists; pair it with the matching SFX bed and the pipeline loops
it to length (1/3/8h), −14 LUFS, seamless. Lead with the keyword; place name is
seasoning; modifier reflects our edge.

## Audio sources (royalty-free, ToS-safe, monetization-OK)

- **Pixabay Sound Effects** (pixabay.com/sound-effects) — truly free, **no
  attribution**, commercial use OK. **Best default.** Has long "rain and fireplace,"
  "rain thunder," "fireplace," "blizzard wind" loops.
- **Freesound.org** — filter license = **Creative Commons 0 (CC0)** for no-attribution.
- **YouTube Audio Library** (in Studio) — free; some tracks need attribution (check).
- Avoid BBC SFX / Zapsplat free tier for monetized use (attribution / license limits).

Tip: grab ONE long high-quality bed per video if you can (e.g. a 1–3h "rain +
fireplace" from Pixabay); otherwise layer 2–3 clips — the pipeline mixes + loops.

## The 5 launch videos

| # | Scene (clip) | Title | Length | SFX to grab (search terms) |
|---|---|---|---|---|
| 1 | snowy_cabin_exterior ❄️ | **Gentle Snowfall & Crackling Fireplace for Deep Sleep \| Cozy Canadian Rockies Cabin \| 8 Hours** | 8h | "blizzard wind loop", "winter wind howling", "fireplace crackling" — **NO rain** |
| 2 | cabin_window_glow_rain 🌧️ | **Heavy Rain & Distant Thunder for Deep Sleep \| Pacific Northwest Cabin \| 8 Hours** | 8h | "heavy rain loop", "distant thunder rumble", "rain on roof", + faint "fireplace crackle" |
| 3 | frozen_lake_cabin 🏔️ | **Snowfall & Fireplace Sounds for Sleeping \| Norwegian Fjord Cabin \| 3 Hours** | 3h | "gentle wind ambience", "fireplace crackling" — **NO rain** |
| 4 | porch_storm ⛈️ | **Rain & Thunderstorm Sounds for Sleep & Relaxation \| Scottish Highlands Cabin \| 8 Hours** | 8h | "rain on roof porch", "rolling thunder", "thunderstorm loop" |
| 5 | fireplace_closeup 🔥 | **Crackling Fireplace Sounds for Sleep & Relaxation \| Cozy Cabin \| 10 Hours (Cinematic)** | 10h | "fireplace crackling 1 hour", "campfire crackle loop", + faint "light rain" |

(The pipeline fills `{dur}` and rotates locations automatically; these are the
human-readable versions for launch.)

## Drip plan (anti-spam)

Don't publish all 5 at once. Space them: **1 video every 1–2 days**, jittered
publish times (the uploader does this). Start with #1 or #2 (highest search volume:
"rain" + "fireplace"). Add 3–5 Shorts/week (10–30s vertical cuts of these clips +
a hook) to drive subs toward YPP.

## Per-video workflow (once the channel is connected)

```
1. Drop the SFX bed:  faceless_fleet/output/raw/rain_cabin/bed.wav
2. python -m faceless_fleet.pipeline.run assemble rain_cabin --variant 8h
3. python -m faceless_fleet.pipeline.run review  rain_cabin        # you approve
4. python -m faceless_fleet.pipeline.run approve rain_cabin --file <name>.mp4
5. python -m faceless_fleet.pipeline.run upload   rain_cabin --dry-run  # then live
```

I drive 2–5 on the VPS once you're connected; you just bless the queue.
