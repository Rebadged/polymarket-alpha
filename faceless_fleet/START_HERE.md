# START HERE — running the "Comforts" fleet

This is the one doc to read first. It gets you from a fresh checkout to a fleet that
**makes, schedules, and uploads videos every week on its own**. Everything else (README,
AUTONOMY, FLEET, BRANDING, deploy/*) is detail you can dip into when a step says so.

## The mental model (read this once)

The system splits into two loops that meet at one folder — the clip library:

```
   RESTOCK (occasional, needs an agent)            PUBLISH (forever, pure cron)
   batch-plan -> Higgsfield -> download   ──▶   assets/clips/<slug>/   ──▶   weekly
        a budgeted batch of silent clips          (the shared library)        pick clip
        deploy/COWORK_RESTOCK.md                                              + seasonal bed
                                                                             + assemble 8h
                                                                             + upload private
                                                                               @ jittered time
```

- **PUBLISH is 100% deterministic** — no tokens, no agent. One cron line (`weekly`) walks
  every connected channel and schedules its week. This is the part that "runs everything
  automatically on a schedule." It only *consumes* clips.
- **RESTOCK is the one step that needs Higgsfield** (an agent today, or an API key). You do
  it occasionally — a library of ~8–12 clips per channel lasts weeks because the loop
  reuses clips least-recently-used first.

That separation is deliberate: it means the money-making loop never depends on an agent
being awake. You stock the shelf now and then; the shop runs itself.

---

## Phase 0 — one-time machine setup (~15 min)

On the VPS (Chicago box) or your PC:

```bash
git clone <repo> /opt/comforts-fleet && cd /opt/comforts-fleet
python3 -m venv venv && ./venv/bin/pip install -r faceless_fleet/requirements.txt
# ffmpeg must be on PATH:  apt install ffmpeg   (Linux)  /  winget install Gyan.FFmpeg (Win)
ffmpeg -version >/dev/null && echo "ffmpeg OK"
```

Sanity check the wiring (no network, no tokens needed):

```bash
./venv/bin/python3 -m faceless_fleet.pipeline.run channels                  # lists the 3 channels
./venv/bin/python3 -m faceless_fleet.pipeline.run batch-plan rain_cabin --budget 16   # writes a manifest, no network
```

---

## Phase 1 — connect Cabin Comforts and publish its first batch

Cabin already has clips + audio + a locked look. Get it live first; the other two are copies.

1. **Create the channel + brand it.** Make a dedicated Google/Brand account, create the
   YouTube channel, **phone-verify it** (required for scheduling). Upload the avatar +
   banner from your Higgsfield library — see **BRANDING.md** for specs and where they go in
   Studio. Set the bio and the Featured-channels cross-links.
2. **One-time OAuth** (gets the refresh token). Follow **deploy/GOOGLE_CLOUD_OAUTH_SETUP.md**
   to make the Desktop OAuth client, then from a machine with a browser:
   ```bash
   ./venv/bin/python3 -m faceless_fleet.pipeline.upload rain_cabin --auth
   ```
   (Headless VPS / phone-only? use `--manual` or `--redirect-host` — see
   **deploy/YOUTUBE_AUTH_PHONE.md**.) Put the OAuth app in **"In production"** in the consent
   screen or the token expires in 7 days.
3. **Store the token as an env var** — never in chat, never in git:
   ```bash
   export YT_RAINCABIN_REFRESH_TOKEN=...   # add to the box's .env that cron sources
   ```
4. **Dry-run the whole loop** (assembles + approves, uploads nothing):
   ```bash
   ./venv/bin/python3 -m faceless_fleet.pipeline.run weekly --channels rain_cabin --dry-run
   ```
   Watch one 8h video build under `output/`. Eyeball it: loudness steady, loop seam
   invisible, audio matches the scene's weather/season.
5. **Go live for real:**
   ```bash
   ./venv/bin/python3 -m faceless_fleet.pipeline.run weekly --channels rain_cabin
   ```
   It uploads as **private with a future publishAt** — your safety net. Check them in
   Studio; they flip public on schedule.

---

## Phase 2 — stand up Campfire + Tent

Same as Phase 1, repeated. Configs, scenes, seasonal audio, and branding already exist
for `campfire` and `camping_tent`. For each:

- Create + phone-verify the channel, upload its avatar/banner (BRANDING.md), cross-link the
  sisters.
- OAuth: `upload campfire --auth` / `upload camping_tent --auth`.
- Export the token to `YT_CAMPFIRE_REFRESH_TOKEN` / `YT_TENT_REFRESH_TOKEN`.

`weekly` auto-detects them: a channel is "connected" the moment its token env var is set,
and skipped (not errored) when it isn't. So you can wire all three and bring them online one
at a time.

---

## Phase 3 — set and forget

Install the cron (one line does the whole fleet's week):

```bash
crontab faceless_fleet/deploy/crontab.example   # after editing REPO= and the env vars
```

That's the finish line: every Sunday it schedules the week for every connected channel,
each video at its own jittered time so nothing bulk-drops. **You never touch the publish
loop again.**

The only recurring chore is **occasionally restocking clips** so visuals stay fresh:
open **deploy/COWORK_RESTOCK.md**, paste the prompt into Cowork, name a channel. It runs
`batch-plan` (a budgeted manifest — default ~20 clips for 160 credits) and generates +
downloads them. Or, for fully unattended restock, set `generation.backend: rest` with a
`HIGGSFIELD_API_KEY` and uncomment the `batch-plan` cron line.

---

## Cheat sheet

| Want to… | Command |
|---|---|
| See configured channels | `run channels` |
| Schedule the week (all connected) | `run weekly` |
| Schedule one channel, no upload | `run weekly --channels rain_cabin --dry-run` |
| Single zero-touch video now | `run auto rain_cabin --publish` |
| Plan a budgeted clip batch | `run batch-plan rain_cabin --budget 160` |
| Restock those clips (agent) | paste deploy/COWORK_RESTOCK.md into Cowork |
| Refresh CC0 audio | `run fetch-sfx --count 3` |
| One-time channel OAuth | `python -m faceless_fleet.pipeline.upload <slug> --auth` |

## Where secrets live (never in chat or git)

Refresh tokens, the Google password, `client_secret*.json`, `token*.json`, and any API key
live **only** in the box's env / `.env` (all gitignored). The repo carries config + code,
never credentials.
