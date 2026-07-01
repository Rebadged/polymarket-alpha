# COWORK HANDOFF — "Comforts" ambient-YouTube fleet

You are picking up a project to launch a small fleet of **faceless ambient-YouTube
channels** (cozy looping sleep/study/relaxation videos). The previous agent (Claude Code
on the web) built the entire pipeline but was **sandboxed** — it could not download media,
drive a browser, or reach the user's machine. **You (Cowork) can do all three**, so you
are the agent that actually ships this: generate → download → assemble → create/brand the
channels → authenticate → upload. Run on the user's PC.

The user is **CK** (Canada). Goal: 2–5 channels, fully automated, revenue from ambient
content. Quality bar he set, in priority order: **audio is the star** (people sleep/study
to it — consistent, startle-proof loudness, no perceptible loop), **visual is the hook**
(stylized painterly cozy, not photoreal), **lean token spend**.

---

## 1. What you can do that the prior agent could not

Route these to yourself — they were the hard blockers:

- **Drive the browser** → create YouTube channels, pick handles, phone-verify, upload
  avatars/banners, set bios + "Featured channels" cross-links, click through Google OAuth
  consent, and download branding from the Higgsfield library.
- **Download media** → the prior sandbox got `403 CONNECT` on Higgsfield's CDN
  (`*.cloudfront.net`) and `platform.higgsfield.ai`. Your machine has normal internet —
  you can pull generated stills/clips and assemble them.
- **Run ffmpeg locally** → do the actual long-form assembly + loudness + seamless loop.
- **Use the Higgsfield MCP** (same connector the prior agent had) → generate images,
  videos, and audio. So you can make banners, avatars, scene clips, etc. directly.

You have both: **MCP generation** AND a **machine to realize it on**. That's the whole job.

---

## 2. Accounts & assets inventory

- **Higgsfield**: Plus plan, ~**894 credits** as of last check. Connected via MCP
  (`generate_image` = `soul_2`; `generate_video` = `kling3_0_turbo`, ~7.5 cr/clip;
  `generate_audio` = TTS only, NOT ambient SFX). Also a **Cloud-API key** exists in the
  env var `HIGGSFIELD_API_KEY` (64-hex single credential) for the optional unattended REST
  path — you don't need it if you generate via MCP.
- **YouTube**: channels **not created yet**. Three planned (see configs). Use **Brand
  Accounts** (separate from CK's personal name); ideally a distinct email per channel for
  hygiene, but one Google account with 3 brand channels is fine to start.
- **VPS**: a Hetzner box exists (`87.99.151.35`, Ubuntu, 3 vCPU / 4 GB / 80 GB) but is
  **not set up** — SSH is key-only (password disabled) and CK couldn't get in from mobile.
  Leave it for last; it's only needed for hands-off scheduling, and your PC can do
  everything else now.
- **Repo**: `Rebadged/Faceless_fleet` (default branch `main`). The `faceless_fleet/`
  package sits at the repo root, so all commands run as `python -m faceless_fleet.pipeline.run …`.
- **Branding already generated** (in the Higgsfield library — verify/re-display with
  `show_generations` or `job_display`, then download from the browser):
  - Tent banner `150bbf37-932c-442d-98a2-edbdf23e291d`, Tent avatar `23c21ead-efec-46d3-9247-1135d870b2bf`
  - Campfire banner `42673481-8378-481b-b532-d092f56be7dc`, Campfire avatar `db810393…`
  - Cabin avatar + banner were generated earlier; Cabin reference still `047a7022`.
  - Regenerate any that are missing/weak using the prompts in `BRANDING.md` + the channel
    `identity` block. Specs: avatar 2048×2048 (reads in a circle), banner **2048×1152**,
    no baked-in text.

---

## 3. The repo

```bash
git clone https://<GITHUB_READ_TOKEN>@github.com/Rebadged/Faceless_fleet.git
cd Faceless_fleet
python3 -m venv venv && ./venv/bin/pip install -U pip -r faceless_fleet/requirements.txt
# ffmpeg must be on PATH (winget install Gyan.FFmpeg on Windows; apt install ffmpeg on Linux)
```

CK is on **Windows** (PowerShell). Note the lessons in §7 about ffmpeg PATH and UTF-8 BOM.

**Pipeline modules** (`faceless_fleet/pipeline/`):
- `config.py` — loads `config/global.yaml` + `config/channels/<slug>.yaml` (deep-merged).
- `generate.py` — builds Higgsfield job specs (still + motion prompts) from a scene + the
  channel's locked look tokens; `choose_title()` for titles.
- `assemble.py` — the ffmpeg core: seamless video loop (`make_seamless_video`), seasonal
  SFX bed (`build_sfx_bed` + `merge_audio_layers`), seamless + loudness-normed audio
  (`make_seamless_audio`), `loop_to_length` (lossless `stream_loop -c copy`), `mux`.
- `auto.py` — zero-touch single run: pick an unused clip → bed → assemble → approve → upload.
- `weekly.py` — set-and-forget: for every connected channel, `restock-fetch` then publish
  `cadence.uploads_per_week` videos. The VPS cron entrypoint.
- `restock.py` — clip transport (record URLs → `restock/<slug>.json`; `fetch_pending`
  downloads them). `rest.py` — unattended Cloud-API generation (`restock-run`).
- `batch_plan.py` — budgeted "what clips are missing" manifest.
- `upload.py` — YouTube OAuth (`interactive_auth`) + scheduled (private + `publishAt`) upload.
- `run.py` — CLI: `generate | assemble | review | approve | upload | auto | weekly |
  batch-plan | restock-record | restock-fetch | restock-run | fetch-sfx | channels`.

**Channels** (`config/channels/`): `rain_cabin` (Cabin Comforts), `campfire` (Campfire
Comforts), `camping_tent` (Tent Comforts). Each has the locked `identity` (look/negative/
motion), a `scene_pool` (scene = focal point × weather, each with `audio_layers`),
`season_audio` palettes, `cadence`, `bio`, `metadata` (title templates / description /
tags), and `youtube_handle`.

---

## 4. Current state

- ✅ Full pipeline built + the ffmpeg core proven on a real long-form render earlier.
- ✅ 3 channel configs with locked look, scenes, seasonal audio, bios, metadata.
- ✅ Branding assets generated (see §2) — need downloading + uploading to YouTube.
- ✅ Two restock paths: MCP scheduled-session (`RESTOCK_SCHEDULE.md`) and unattended REST
  (`REST_SMOKE_TEST.md`, `restock-run`). REST needs its 2 Cloud-API model slugs confirmed
  on a real-internet machine (you) — `deploy/probe_slugs.py --write` does it in one run.
- ❌ No YouTube channels created yet.
- ❌ No clips downloaded / no finished videos / nothing uploaded.
- ❌ VPS not set up (last priority).

---

## 5. Your playbook (in order)

### A. Set up locally
Clone + venv + ffmpeg (§3). Confirm `./venv/bin/python -m faceless_fleet.pipeline.run channels`
lists the three channels.

### B. Branding (browser + MCP)
For each channel: pull its avatar + banner from the Higgsfield library (§2), or regenerate
weak ones with the `BRANDING.md` prompts. Save the files locally for upload in step C.
Then read **`BRANDING.md` → "Thumbnail & brand system"** (distilled from
`research/BRANDING_PLAYBOOK.md`) and build **2–3 thumbnail templates per channel**
(1280×720, one fixed utility tag like "RAIN & THUNDER" / "10 HOURS" in a bold condensed
font, image-forward, warm/cool contrast). Thumbnails are a **compositing step** (Pillow/
ffmpeg/Canva over the scene still) — never an AI render with baked text. Pick the fleet
font once (Bebas Neue / Anton / Oswald Bold / Montserrat ExtraBold).

### C. Create + brand the channels (browser) — **do Cabin Comforts fully first**, then clone
> **Launch staging (see ROADMAP → "Channel-launch staging"):** create + brand **all 3 now**
> (they age + are ready), but only Cabin **uploads at full cadence** at first. Start a light
> trickle (~1–2/wk) on Campfire + Tent once Cabin is ~2–4 weeks clean/unflagged (Gate A);
> full cadence on them after Cabin proves monetization (Gate B, ~90 days/YPP). Don't flood
> all three day one; don't freeze 2 & 3 fully dormant either.
1. Create the channel as a **Brand Account** (YouTube → Settings → Add/manage channels →
   Create a channel). Name from the config (`channel.name`).
2. **Handle**: try `@CabinComforts`; if taken use `@CabinComfortsTV` / `…ASMR` / `The…`.
   Whatever you land on, **write it back into the config** (`youtube_handle`) and commit.
3. **Phone-verify** (youtube.com/verify) — CK enters the SMS code. Needed for scheduling.
4. **Branding** (Studio → Customization → Branding): upload avatar + banner.
5. **Basic info**: paste `channel.bio` as the description; set country = Canada (or US for
   CPM — CK's call). Add a **Featured channels** section linking the sister Comforts
   channels once they exist (cross-discovery — a core part of the strategy).
6. Repeat for Campfire Comforts and Tent Comforts.

### D. Audio elements (one-time)
The seasonal beds need a few CC0 SFX files in `faceless_fleet/assets/sfx/` (rain_tent,
rain_light, fireplace, wind, crickets, frogs, thunder, lake_water…). Either run
`run fetch-sfx --count 3` (needs a free `FREESOUND_API_KEY`) or drop in hand-picked CC0
files. Filenames map via each channel's `audio.sfx_library`. CK's audio notes: tent =
**rain ON the tent/tarp** (the drum), fire = light **drizzle not downpour**, summer adds
**crickets + frogs**.

### E. Generate + assemble the first videos
1. `run batch-plan rain_cabin --budget 56` → read the manifest; for each item generate the
   still (`soul_2`) then animate it (`kling3_0_turbo`, **camera locked**, 10s), download the
   MP4 to `assets/clips/rain_cabin/<clip_name>`.
2. `run auto rain_cabin --variant 8h` (no `--publish` yet) → builds the seasonal bed, makes
   the seamless loop, assembles an 8-hour video into `output/pending_review/`.
3. **Watch it with CK's bar in mind**: loudness steady (no startle), loop seam invisible,
   audio matches the scene's weather/season, source motion >40s feel so it doesn't read as
   a loop. Iterate the clip/bed if not.

### F. Upload (private + scheduled)
1. One-time OAuth: follow `deploy/GOOGLE_CLOUD_OAUTH_SETUP.md` (Desktop OAuth client,
   publish status "In production" so the token doesn't expire in 7 days), then
   `python -m faceless_fleet.pipeline.upload rain_cabin --auth`. Store the refresh token in
   the env var `YT_RAINCABIN_REFRESH_TOKEN` (see §8 — never in chat/git).
2. `run auto rain_cabin --variant 8h --publish` (or `run upload rain_cabin`) → uploads
   **private with a future `publishAt`** (the scheduled-private window is the safety net;
   it flips public on schedule). Confirm in Studio.

### G. Automation (last, optional)
Once a channel is proven end-to-end, move the recurring loop to the Hetzner VPS:
`weekly` on cron + the restock schedule. See `START_HERE.md` §Phase 3, `RESTOCK_SCHEDULE.md`,
`deploy/crontab.example`. The VPS needs first-time access fixed (SSH is key-only — add CK's
public key via the Hetzner web console, or enable password auth). Not needed to launch.

---

## 6. Creative & quality spec (the locked look — do not drift)

- **Look**: cinematic **stylized painterly realism**, idealized cozy — NOT photoreal, NOT
  cartoon. Hides AI artifacts, more ownable. Per channel see `identity.film_look`.
- **Composition**: focal point (cabin/campfire/tent) in an **open clearing**, **dense
  forest as a backdrop behind it** — *no foreground tree trunks* (CK rejected those
  repeatedly), warm glow vs cool night. Keep scenes **sparse** (few objects → fewer
  gibberish artifacts). Always append the channel's `identity.negative`.
- **Motion**: camera **locked/static**; the loop comes from the **ambient element**
  (falling snow/rain, dancing fire, flickering lantern), never camera movement.
- **Audio philosophy** (the product): the focal sound + the season's palette
  (`season_audio`). Tent = rain-on-tent drum; fire = drizzle not downpour; summer =
  crickets + frogs. Source files long (>40s) so the loop is imperceptible.
- **Loudness (startle-proof, consistent across every video)**: target **−14 LUFS**
  (YouTube's normalization point → no volume jump between videos), true-peak **−1.5 dBTP**
  hard cap, loudness range **6 LU** (tight, no swells). Already wired in `global.yaml`
  `assembly` + `make_seamless_audio`. Do not loosen — a thunderclap must never spike.
- **Loop illusion**: seamless xfade-wrap on both video and audio so the seam is invisible
  across hours; long source elements so nothing obvious repeats.
- **Thumbnails & brand system** (see `BRANDING.md` → "Thumbnail & brand system"): locked
  per-channel grade + ONE condensed font + object/glyph avatar (reads at 98px) + 2–3
  reusable templates. Ambient = image-forward with ONE utility tag (declares format, not
  mood), bottom-/top-left, never bottom-right. Banner safe area 1546×423 (wordmark to
  1235×338), bottom-left clear. **Material-variation rule**: keep the frame consistent,
  make every video's scene/audio/title genuinely distinct (the `review.py` gate enforces
  this — it's the inauthentic-content compliance keystone).

---

## 7. Gotchas & lessons learned (save yourself the pain)

- **Sandbox egress** (why you exist): the prior agent got `403 CONNECT` to
  `*.cloudfront.net` and `platform.higgsfield.ai`. You're on a real machine — fine.
- **UTF-8 BOM**: PowerShell `Set-Content -Encoding utf8` writes a BOM that broke JSON
  parsing ("Expecting value: char 0"). All pipeline JSON reads use `encoding="utf-8-sig"`;
  when YOU write JSON/YAML on Windows use `[System.IO.File]::WriteAllText(path,text)` or
  ensure no BOM.
- **ffmpeg PATH**: "WinError 2" = ffmpeg not found. `winget install Gyan.FFmpeg` then
  **reopen** the shell so PATH refreshes.
- **acrossfade starves** if fed two atrim branches of the same source — `make_seamless_audio`
  already works around it (extracts head/tail to temp WAVs). Don't "simplify" it back.
- **Long-form must be `stream_loop -c copy`** (encode the short unit ONCE, then loop
  losslessly) — re-encoding 8h will time out. Already done; preserve it.
- **Higgsfield**: `generate_audio` is **TTS only** — get ambient SFX from Freesound (CC0),
  not Higgsfield. Kling = locked camera, `start_image`, duration 3–15s.
- **Cloud-API slugs ≠ MCP names**: `soul_2`/`kling3_0_turbo` are MCP IDs; the REST Cloud
  API uses fal-style slugs (`provider/model/task`). Only matters for `restock-run`;
  `probe_slugs.py` discovers them.

---

## 8. Security rules (non-negotiable)

- **Never** put a Google password, YouTube refresh token, or API key **in chat or in git**.
  They live only in env vars / a local `.env` (gitignored). `client_secret*.json` and
  `token*.json` are gitignored.
- Refresh tokens go in the per-channel env vars (`YT_RAINCABIN_REFRESH_TOKEN`,
  `YT_CAMPFIRE_REFRESH_TOKEN`, `YT_TENT_REFRESH_TOKEN`).
- The GitHub token for cloning should be **read-only, this repo only**. If any secret lands
  in chat by accident, regenerate it.
- Upload posture is **private + scheduled `publishAt`** (auto-flips public). Keep it.
- You **cannot create Google accounts** for CK (ToS) — he creates them; you drive the
  browser through setup with his confirmation on anything irreversible (publishing,
  deleting, account changes).

---

## 9. Doc map

- `START_HERE.md` — master runbook (two-loop model, connect a channel, go live, cron).
- `BRANDING.md` — avatar/banner/thumbnail specs, the locked brand system, the
  material-variation compliance checklist, per-channel prompts + Studio upload steps.
- `research/BRANDING_PLAYBOOK.md` — full branding/visual-identity research (thumbnail
  formulas by niche, naming, YouTube specs, inauthentic-vs-reused policy, RPM economics).
- `research/RESEARCH_BACKLOG.md` — open deep-dives (audio sourcing/licensing, SEO,
  growth/live/Shorts, monetization + CA tax). Findings land in `research/` then fold into
  the relevant doc. **Weighting rule: back fleet/niche research; do NOT over-weight the
  old "2am" experiment's character-specific data.**
- `research/CROSS_REFERENCE_2026.md` — **READ THIS** before generating/uploading: a second
  model's 2026 validation reconciled against our build. Corrects the Higgsfield credit math
  (now ~17 cr + 3× iteration per 10s clip, not 8), the hidden YouTube upload cap (≤5/day on
  unverified projects → 429), and surfaces 3 open CK decisions (5s vs 10s clips; locked
  camera + particle overlays vs added motion; Suno music vs pure CC0 ambience). Backs the
  source dossiers `2026_strategic_validation_canada.md` + `2026_fleet_research_dossier.pdf`.
- `deploy/GOOGLE_CLOUD_OAUTH_SETUP.md`, `deploy/YOUTUBE_AUTH_PHONE.md` — YouTube auth.
- `deploy/RESTOCK_SCHEDULE.md` — weekly restock (scheduled session + git bridge).
- `deploy/REST_SMOKE_TEST.md` + `deploy/probe_slugs.py` — confirm Cloud-API slugs (REST).
- `deploy/COWORK_RESTOCK.md` — budgeted clip-restock prompt.
- `deploy/crontab.example` — the VPS cron (one `weekly` line).
- `AUTONOMY.md`, `FLEET.md`, `ROADMAP.md`, `LAUNCH_PLAN.md` — strategy/background.

**First action:** read this file + `START_HERE.md`, clone the repo, then start §5.A. Launch
**Cabin Comforts** end-to-end before touching the others. Keep CK in the loop on anything
that publishes or spends meaningful credits.
