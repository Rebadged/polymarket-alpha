# Cabin Comforts — Launch Plan (calendar + Shorts hooks + audio picks)

Companion to LAUNCH_SLATE.md. Everything here is phone-doable; the audio you can
grab on Pixabay right now.

## 1. Audio: how to pick a bed on Pixabay (phone)

Go to **pixabay.com/sound-effects/** (free, no attribution, commercial-OK). For each
video grab ONE long bed if possible, else 2 clips and the pipeline mixes them.
Selection rules:
- **Long** (10+ min ideal; the pipeline loops anyway, but longer = fewer seams).
- **No music / no melody** — pure ambience.
- **No voices, no birds/animals**, no sudden bangs.
- Download the **MP3/WAV**; later it goes to the VPS as `bed.wav`.

| Video | Pixabay searches (grab + combine) |
|---|---|
| Rain (PNW) | **"rain and thunder"**, "heavy rain loop", "rain ambience" + optional "fireplace" |
| Snowfall (Rockies) | **"blizzard wind"**, "winter wind howling", "snow storm wind" + **"fireplace crackling"** (no rain) |
| Thunderstorm (Highlands) | **"thunderstorm"**, "rain on roof", "rolling thunder" |
| Snowfall+Fire (Norway) | "winter wind", **"fireplace crackling"** (no rain) |
| Fireplace (10h) | **"fireplace crackling"**, "campfire crackle", + faint "light rain" |

Tip: search **"rain fireplace"** and **"crackling fire"** — Pixabay has several
multi-hour beds that work as-is. Save them in a folder; we move them to the VPS together.

## 2. Two-week launch calendar (drip — never bulk-publish)

Long-form: ~3/week, jittered times (uploader randomizes within an evening slot).
Lead with the highest-search weather first. Shorts: 4–5/week feeding the funnel.

| Day | Long-form (8h unless noted) | Shorts |
|---|---|---|
| 1 | **Heavy Rain & Distant Thunder — Pacific Northwest** | Short A |
| 2 | — | Short B |
| 3 | **Crackling Fireplace — Cozy Cabin (10h)** | — |
| 4 | — | Short C |
| 5 | **Rain & Thunderstorm — Scottish Highlands** | Short D |
| 7 | **Gentle Snowfall & Crackling Fireplace — Canadian Rockies** | Short E |
| 9 | **Snowfall & Fireplace — Norwegian Fjord (3h)** | Short F |
| 11 | New location of the rain scene (e.g. British Columbia) | Short G |
| 13 | New location of the snow scene (e.g. Swiss Alps) | Short H |

After day 13 the pipeline keeps rotating scene × location so every upload differs.
Weight snow/cozy heavier as you head into NH autumn/winter + Q4 (CPM premium).

## 3. Shorts hooks (10–30s vertical cut of a clip + text overlay)

Cut a vertical (9:16) slice of any cabin clip, add ONE line of text, soft music or
the ambience. Categories from your hook library:

**Curiosity gap**
- "POV: it's storming outside but you're warm inside 🌧️"
- "the coziest place on earth might not be real…"
- "the sound that knocks me out in 5 minutes"

**POV / immersive**
- "POV: you finally made it to the cabin"
- "POV: snowed in, nowhere to be, nothing to do"
- "rainy nights hit different from a cabin"

**Bold statement**
- "this is the only thing that puts me to sleep anymore"
- "8 hours of rain > any sleeping pill"

**FOMO / save-bait**
- "save this for your next sleepless night"
- "you'll wish you found this sooner"

**Comment bait**
- "rain or snow to fall asleep to? 👇"
- "drop a 🔥 if you'd live here"

Rotate categories; don't reuse the same hook twice. End each Short by pointing to
the full-length video ("full 8-hour version on the channel").

## 4. YouTube settings to flip once the channel's live (from research)

- **Monetization** later (need 1k subs + 4k hours): ad config = **pre-roll on,
  mid-rolls OFF, post-roll OFF** on the sleep-length videos.
- **Playlists:** "Rain for Deep Sleep", "8-Hour Storms", "Snowy Cabin Nights" —
  add each video to one; enable autoplay (chains the night = more watch-hours).
- **Upload defaults** (Studio → Settings → Upload defaults): paste the description +
  tags so every upload inherits them.
- **AI disclosure:** not required for stylized ambient (non-realistic). Leave off.

## 5. What still needs your PC (when ready)

1. Mint the refresh token (client_secret.json + the auth helper) — born on the VPS.
2. VPS setup: clone the repo, install ffmpeg + deps, set the token env var.
3. Move your Pixabay beds to the VPS.
Then I assemble → you approve → we drip-publish.
