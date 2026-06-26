# Autonomy: how Cabin Comforts runs itself

The goal: after setup, **you touch nothing day-to-day.** The trick is splitting
work into a rare "stock-up" and a daily zero-touch loop.

```
  STOCK UP  (every few weeks, assisted)        DAILY LOOP  (zero-touch, cron)
  ─────────────────────────────────────        ──────────────────────────────
  • batch-generate clips  -> clip library      auto:
  • fetch-sfx (one time)  -> audio library       1. pick next unused clip (rotates scene+location)
                                                 2. build audio bed from SFX library
                                                 3. assemble -> 8h, seamless, -14 LUFS
                                                 4. approve (auto)
                                                 5. upload PRIVATE + jittered publishAt
```

Last night felt manual because we hand-placed one clip and named files by hand.
The loop never does that — it pulls from **libraries** and handles every path/name.

## The daily loop (the whole thing)

```bash
python -m faceless_fleet.pipeline.run auto rain_cabin --publish
```
That one command = a finished, scheduled YouTube video. On the VPS it's one cron
line on a jittered cadence (see deploy/crontab.example). No paths, no filenames,
no downloads.

## What you stock up (rarely)

### 1. Audio library — ONE TIME, automated
```bash
# set FREESOUND_API_KEY first (free: https://freesound.org/apiv2/apply/)
python -m faceless_fleet.pipeline.run fetch-sfx
```
Auto-downloads CC0 (license-clean) rain/thunder/fire/wind into `assets/sfx/` with
the exact names the pipeline expects. Audio elements are REUSABLE forever, so this
is basically once. Re-run with `--count 3` to pull variants for variety later.

### 2. Clip library — every few weeks
Pre-generated clips live in `assets/clips/<slug>/<scene_id>__<name>.mp4`. The loop
rotates through them (scene × location = lots of distinct videos from a few clips).
Three ways to stock it — pick per your autonomy appetite:

- **A. Claude/Cowork batch (now):** I generate a batch via Higgsfield, you (or a
  Cowork session on the VPS) download the result URLs into the clip library. ~30
  clips = weeks of content. Lowest setup, mild human touch every few weeks.
- **B. Cowork scheduled task:** a recurring Cowork task on the VPS calls Higgsfield
  + drops clips into the library on a schedule — hands-off generation.
- **C. Higgsfield REST API (if available):** wire `generation.backend: rest` +
  `HIGGSFIELD_API_KEY` so the VPS generates with no agent at all. Fully unattended
  end-to-end. (Verify Higgsfield offers API keys before relying on this.)

> For an ambient channel you do NOT need fresh generation per video — the same
> clips loop for hours and rotate by scene/location, so a periodic batch is plenty.

## The one honest caveat

Everything except **clip generation** is fully deterministic and unattended. Image/
video generation needs a model (Higgsfield), which is either a periodic batch
(A/B) or an API (C). Audio, assembly, scheduling, and upload are 100% hands-off.

## Review posture (your call)

`auto.auto_approve: true` (default) skips the manual gate; videos upload as
**private + publishAt**, so they sit scheduled — a built-in safety window where you
*can* glance before they go public, but they'll publish on their own if you don't.
Set `auto_approve: false` to require you to approve each one (uploads wait in
`approved/`). Per-video variation (scene/location/audio rotation) is what keeps the
channel policy-safe — not human review.

## VPS deploy (the always-on home)

```bash
# one time on the Chicago VPS
git clone -b <branch> <repo> && cd polymarket-alpha
sudo apt-get install -y ffmpeg && pip install -r faceless_fleet/requirements.txt
# secrets/env: client_secret.json, YT_RAINCABIN_REFRESH_TOKEN, FREESOUND_API_KEY
python -m faceless_fleet.pipeline.run fetch-sfx          # stock audio
# drop the clip library in assets/clips/rain_cabin/
crontab faceless_fleet/deploy/crontab.example           # the jittered loop
```
The VPS (open egress, always on) downloads clips + runs the loop. This sandbox
can't (egress-restricted) — but it's the builder/supervisor.
