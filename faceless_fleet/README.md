# Faceless Fleet 🌙

A review-gated, config-driven pipeline for ambient/sleep faceless channels.
Built from your two research playbooks. Channel 1 is your existing
**`2am without her`** (ambient/sleep/lofi); Channel 2 is **meditation /
sleep-story narration** (the next lane).

> **Design principle (straight from the research):** Claude/MCP is the *builder*
> and *generation touchpoint*; deterministic Python (ffmpeg + YouTube API) runs
> the unattended loop; **one human quality gate** sits between
> `pending_review/` and `approved/`. Nothing publishes blind.

---

## Pipeline at a glance

```
generate ─▶ [Higgsfield: image ▶ video ▶ audio] ─▶ assemble (ffmpeg) ─▶ pending_review/
                                                                            │  ← YOU approve
                                                                            ▼
                                                          approved/ ─▶ upload (YouTube private+publishAt)
```

| Stage | Module | Credits? | Runs where | Status |
|-------|--------|----------|------------|--------|
| 1. generate | `pipeline/generate.py` | **Higgsfield credits** | MCP session / VPS | ✅ built, ⏳ needs credits |
| 2. assemble | `pipeline/assemble.py` | none | VPS (heavy) | ✅ **working & proven** |
| 3. review   | `pipeline/review.py`   | none | anywhere | ✅ working |
| 4. upload   | `pipeline/upload.py`   | none | VPS / Actions | ✅ built, ⏳ needs YouTube OAuth |

The deterministic core (assemble → review → upload-dry-run) is **validated
end-to-end**: a 3-hour loop renders in ~60s via ffmpeg stream-copy, the review
gate flags sub-8-minute/duplicate videos, and the uploader produces a correct
scheduled-publish request with jittered `publishAt`.

---

## Commands

```bash
pip install -r faceless_fleet/requirements.txt      # + system ffmpeg

python -m faceless_fleet.pipeline.run channels                 # list channels
python -m faceless_fleet.pipeline.run generate 2am_without_her # -> raw/jobs.json manifest
#   (fulfil jobs.json via Higgsfield MCP, then:)
python -m faceless_fleet.pipeline.run assemble 2am_without_her --variant 3h
python -m faceless_fleet.pipeline.run review   2am_without_her           # list + policy flags
python -m faceless_fleet.pipeline.run approve  2am_without_her --file X   # the human gate
python -m faceless_fleet.pipeline.run upload    2am_without_her --dry-run # then drop --dry-run
```

Everything is driven by `config/global.yaml` + `config/channels/<slug>.yaml`.
Add a channel = add one YAML file (copy `2am_without_her.yaml`).

---

## How generation actually works (two backends)

Higgsfield's generators are an **MCP server** today — callable by a Claude
session, not by a bare cron job. So `generate.py` has two modes
(`generation.backend` in `global.yaml`):

- **`manifest`** (default, works now, no API key): writes `output/raw/<slug>/jobs.json`.
  A Claude Code / Cowork / `claude -p` session fulfils it with `generate_image`
  → `generate_video` → `generate_audio`, dropping files into `raw/`. This keeps
  Claude as the generation touchpoint (which the research recommends anyway).
- **`rest`** (fully unattended, needs `HIGGSFIELD_API_KEY`): calls Higgsfield's
  HTTP API directly so a VPS cron generates with no agent in the loop. The
  endpoint paths in `higgsfield_client.py` are **stubbed/TODO** — confirm them
  against Higgsfield's API docs before trusting blind automation.

**Models wired (verified live, 2026-06):** stills `z_image` (fast/budget) or
`recraft-v4-1` (photoreal); image→video `grok_video_v15` (Grok Imagine 1.5,
native audio, 2–15s) or `seedance_2_0` (hero/reference). Swap per channel in
the YAML.

---

## ⚠️ Blockers only you can clear

1. **Higgsfield is on the FREE plan with 0 credits** → no image/video/audio can
   be generated yet. The first-video manifest is staged and ready; it renders
   the moment credits land. Research target: **Higgsfield Plus (~$39 USD/mo
   annual, 1,000 credits)**. (Ask me to open the pricing widget.)
2. **YouTube OAuth** → run once locally per channel:
   ```bash
   # put your OAuth "Desktop app" client_secret.json in faceless_fleet/secrets/
   python -m faceless_fleet.pipeline.upload 2am_without_her --auth
   ```
   Store the printed refresh token as the env var / secret named in the
   channel's `oauth_secret_env` (e.g. `YT_2AM_REFRESH_TOKEN`).
3. **Channel must be phone-verified** or `videos.insert` returns 403.

### On "make the emails and channels too"
I can't fully automate this — **Google blocks programmatic account creation**
(phone + CAPTCHA), and creating accounts via automation violates Google's ToS
and risks bans across the fleet. What I *can* do: prep everything around them —
brand names, handles, descriptions, banner/avatar prompts (Higgsfield), the
metadata, and the OAuth wiring. You click through signup (~10 min each); I do
the rest. One Google account can hold multiple YouTube channels (brand
accounts), so you don't need a Gmail per channel.

---

## Orchestration

- **Chicago VPS = the runtime.** `deploy/run_channel.sh` + `deploy/crontab.example`
  run generate→assemble on an off-peak jittered schedule and drip uploads.
  Heavy multi-GB renders belong here, not on CI.
- **GitHub Actions = control-plane.** `.github/workflows/fleet-upload.yml` runs
  the upload drip / manual triggers. (Media isn't in git — the workflow expects
  approved files synced from storage; see the TODO step in it.)

**Anti-spam rules baked in:** `private` + jittered `publishAt`, ≥20h between
uploads, per-video scene/title variation enforced by `state.py` + `review.py`,
drip-not-dump cadence. These directly answer YouTube's July-2025
"inauthentic content" rule.

---

## Setup checklist

- [ ] `pip install -r faceless_fleet/requirements.txt` and install `ffmpeg`
- [ ] Upgrade Higgsfield (Plus) so generation has credits
- [ ] Decide backend: `manifest` (Claude fulfils) vs `rest` (API key)
- [ ] Fill real handle/`youtube_channel_id` in `config/channels/2am_without_her.yaml`
- [ ] Drop your existing `2am without her` track/branding refs into the config
- [ ] Create OAuth "Desktop app" creds → `secrets/client_secret.json`
- [ ] `--auth` each channel → store refresh tokens as secrets
- [ ] Deploy `crontab.example` on the Chicago VPS (adjust `$REPO`)
- [ ] Add GitHub secrets: `YT_CLIENT_SECRET_JSON`, `YT_2AM_REFRESH_TOKEN`, …
- [ ] First real run: generate → fulfil manifest → assemble → review → approve → upload `--dry-run` → upload
