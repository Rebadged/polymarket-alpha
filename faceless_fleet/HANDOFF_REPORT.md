# Faceless Fleet — Build & Validation Report + Creative-Direction Research Brief

> **Purpose of this document.** Two jobs. (1) A complete record of what was built
> and proven in the build session — the pipeline, the architecture, the first
> *real* Higgsfield generation, and every hard fact/constraint discovered. (2) A
> research brief for a deep-research instance to answer the open question the
> operator (CK) is now asking: **"We have the genre — but what are we actually
> creating?"** i.e. the creative identity, positioning, and product strategy.
>
> Date: 2026-06-25 · Repo branch: `claude/faceless-ai-youtube-channels-74t0he`
> Operator: CK (Canada) · Existing live channel: **"2am without her."** (@2amWithoutHer)

---

## PART 1 — Executive summary

- A **review-gated, config-driven content pipeline** was built and committed under
  `faceless_fleet/`. It generates → assembles → schedules-uploads ambient/sleep
  videos, with one human quality gate before anything publishes.
- The **deterministic core is proven**: a 3-hour long-form video assembles from a
  short clip in **~60 seconds** via ffmpeg stream-copy (lossless loop).
- The **generation layer is proven with real output**: Higgsfield (now on a paid
  **Plus** plan, ~1,000 credits/mo) produced an on-brand still of the channel's
  "girl" character in the purple/blue 35mm night aesthetic, then animated it into
  a 5-second cinematic motion clip — the key capability the old static-still
  pipeline lacked. Cost: **~8 credits total** (~0.12/image, 7.5/video clip).
- **Verdict from CK on the example:** "looks okay, looks real… it isn't the same
  girl as the channel but that's okay, it proves the pipeline." → Character
  *consistency* is the known next problem (solvable via Higgsfield Soul ID).
- **The open strategic question** (Part 6) is no longer technical — it's creative:
  what *is* this channel/fleet beyond "sad lofi," and what should it become?

---

## PART 2 — What was built (the system)

Everything lives in `faceless_fleet/` in the repo. Structure:

```
faceless_fleet/
  README.md                         playbook + setup checklist
  HANDOFF_REPORT.md                 this file
  requirements.txt
  config/
    global.yaml                     fleet-wide defaults (models, paths, anti-spam)
    channels/
      2am_without_her.yaml          Channel 1 — the validated brand (full detail)
      midnight_meditations.yaml     Channel 2 — meditation/sleep-story lane (next)
  pipeline/
    config.py        merge global+channel YAML
    state.py         per-channel scene/title de-dup (anti-"inauthentic content")
    generate.py      pick unused scene → Higgsfield job manifest (image→video→audio)
    higgsfield_client.py  manifest backend (MCP) + rest backend (unattended)
    assemble.py      ffmpeg: stream_loop long-form, Ken Burns, bed/narration mix
    review.py        human gate + automated policy checks (8min, dup, COPPA)
    schedule.py      jittered publishAt (anti-spam)
    upload.py        YouTube private+publishAt; phone-friendly OAuth helper
    run.py           orchestrator CLI
  deploy/
    run_channel.sh           VPS: generate→assemble
    fetch_and_assemble.sh    VPS: download Higgsfield outputs + Suno bed → assemble
    crontab.example          VPS cron (jittered, staggered per channel)
    YOUTUBE_AUTH_PHONE.md    phone-based OAuth walkthrough
.github/workflows/fleet-upload.yml  control-plane upload drip
```

**Pipeline flow:**
```
generate ─▶ [Higgsfield image ▶ video ▶ audio] ─▶ assemble(ffmpeg) ─▶ pending_review/
                                                                          │ ← CK approves
                                                                          ▼
                                                  approved/ ─▶ upload (YouTube private+publishAt)
```

**Commands:**
```bash
python -m faceless_fleet.pipeline.run generate 2am_without_her
python -m faceless_fleet.pipeline.run assemble 2am_without_her --variant sleep
python -m faceless_fleet.pipeline.run review   2am_without_her
python -m faceless_fleet.pipeline.run approve  2am_without_her --file <name>.mp4
python -m faceless_fleet.pipeline.run upload    2am_without_her --dry-run
```

**Anti-spam controls baked in** (YouTube July-2025 "inauthentic content" rule):
per-video scene/title rotation (`state.py`), organic non-round durations
(~3:00:28, not 3:00:00), jittered `publishAt`, ≥20h between uploads, private→
scheduled release, drip-not-dump cadence.

---

## PART 3 — The validated test (real generation)

**Goal:** prove Higgsfield can produce the 2am brand and add motion.

**Still — model `soul_2` (Higgsfield Soul v2), 16:9, 2K, ~0.12 credits each (×2):**
Prompt (the channel's verbatim character + scene template, formatted):
> Photorealistic candid photo of young woman with dark brown wavy hair, hoop
> earrings, delicate necklace, natural freckles, standing on a rainy apartment
> balcony at night wrapped in a soft cardigan, blurred purple city lights and rain
> behind her, looking out wistfully, shot on 35mm film, purple and blue ambient
> night lighting, subtle grain, melancholic and intimate — [negative: no visible
> text/signage/labels, no warped hands/extra fingers, no watermarks/logos, no
> heavy VHS/scanline filter]

**Motion — model `kling3_0_turbo`, 5s, 720p, image-to-video, 7.5 credits:**
> extremely slow gentle push-in, rain falling softly behind her, her hair barely
> moving in the breeze, calm and still, cinematic 35mm, no sudden motion

**Result links (public CDN; open on phone — NOT reachable from the build sandbox):**
- Still A (used for clip): `…/hf_20260625_163017_80748b37-…png`
- Still B (alt): `…/hf_20260625_163017_98d1075d-…png`
- Motion clip: `…/hf_20260625_163351_9fdd771a-…mp4`
  (full host: `https://d8j0ntlcm91z4.cloudfront.net/user_3FdTKdOtC6CmqWtVhwJcIt6v5Ik/`)

**What it proves:** the visual + motion quality is publishable-grade and on-brand.
**Known gap:** soul_2 text-to-image does NOT reproduce the *same* girl as the live
channel. Fix = train a **Higgsfield Soul ID** (5–20 reference photos of the
channel's existing girl, one-time ~10 min) so she is identical across every video.
That converts the character from "generic pretty girl" into recognizable channel IP.

---

## PART 4 — Confirmed facts & constraints (hard-won, reusable)

**Higgsfield (live, 2026-06):**
- Plan **Plus** = ~1,000 credits/mo. Image (soul_2, 2K) ≈ **0.12 cr**; Kling 3.0
  turbo video (5s, 720p) ≈ **7.5 cr**. → a full video needs ~8–25 cr incl. rerolls.
- **Credit math favors us:** ambient loops one short clip, so ~40–60 videos/mo of
  capacity on Plus — far more than safe upload cadence (~24/mo for 2 channels).
  **Ultra (3,000 cr) is NOT needed yet**; the bottleneck is YouTube cadence, not credits.
- Higgsfield audio is **TTS-only — no music model** for standalone use. Music must
  come from **Suno** (manual; no official API — ToS-safe path is generate-in-app,
  download WAV).
- Workspace gotcha: the MCP can be authed to a *different* Higgsfield account than
  the one you upgraded. If balance shows free/0, reconnect the connector to the
  upgraded login. Confirmed: only the correct workspace shows `plus` + credits.
- Useful models: image `soul_2` (photoreal portrait/editorial), `soul_cast`
  (character identity), `recraft-v4-1`, `z_image` (fast/budget); video
  `kling3_0_turbo` (cheap workhorse), `seedance_2_0` (hero/native-audio), `grok_video_v15`.

**Environment constraint (important for architecture):**
- The Claude *web/sandbox* session's egress policy **blocks the Higgsfield CDN**
  (403), and the preview-widget tool (`job_display`) is permission-blocked. So the
  sandbox can **drive generation** but cannot **download media** or assemble.
  → The production **runtime is the VPS** (Chicago box, open egress): it downloads
  Higgsfield outputs + the Suno bed and runs ffmpeg. Claude = builder/director;
  deterministic VPS code = the unattended loop. (Matches the research's division of labor.)

**Platform/monetization (Canada-specific, carried from prior research):**
- YouTube = the monetization engine (YPP: 1,000 subs + 4,000 watch-hrs).
- **TikTok Creator Rewards excludes Canada** → TikTok/IG = reach only.
- **Facebook Content Monetization** = best secondary income.
- 2am ad config: **mid-rolls OFF** (preserve listening; overnight autoplay chains
  stack impressions across videos). Other lanes (narration 8+min) may want mid-rolls.

**The validated 2am template (channel-specific, from CK's context doc):**
- Brand: **"2am without her."** (trailing period). Bio: "music for 2am when you
  can't stop thinking about her." Audience: young men who miss someone / can't sleep.
- Aesthetic: purple/blue night, 35mm film, consistent **girl** character, lo-fi warmth.
- The girl (verbatim, every image): *young woman with dark brown wavy hair, hoop
  earrings, delicate necklace, natural freckles.*
- Titles: lowercase, longing, end with `.` or `…`, **no emojis**. e.g. `she felt
  like home.` (hit ~11.1% CTR), `i wish you'd call..`, `she didn't say goodbye.`
- Two lanes: **Sleep/Emotional** (~3h, ultra-slow ambient, no drums) and **Study
  With Me** (~20min, lo-fi groove). Image rule: **no visible text on any surface**.
- Early signal: organic YouTube search traffic within 48h; strong retention.

---

## PART 5 — Status: done vs pending

**Done & committed:** full pipeline; both channel configs; proven ffmpeg core;
proven Higgsfield generation; phone OAuth helper; VPS deploy scripts; GitHub
Actions upload workflow; anti-spam logic.

**Pending (needs CK / human action):**
- Train **Soul ID** for the 2am girl (character consistency) — needs her reference photos.
- Provide a **Suno bed** WAV (manual) for the first full assembly.
- **YouTube OAuth** per channel (Google Cloud project + client_secret.json → token).
- Run first full assembly **on the VPS** (`deploy/fetch_and_assemble.sh`).
- Decide creative direction (Part 6) before scaling to 3–5 channels.

---

## PART 6 — RESEARCH BRIEF: "What are we actually creating?"

CK's framing: *"We have the genre and stuff but I'm not sure what we're actually
going for yet."* The technical pipeline is solved; the **creative product is not
defined**. This is the brief for the deep-research instance. Answer with concrete,
opinionated recommendations, not just options — and ground them in what's working
on YouTube/TikTok in the sad-lofi / ambient / "comfort-core" space in 2026.

**Core question:** Is "2am without her." (and the fleet around it) a *mood-wallpaper
brand*, a *character/story IP*, or a *multi-channel ambient network*? Each implies a
different product, content strategy, and ceiling.

### Strands to research

1. **Identity & positioning.**
   - Map the competitive set ("i miss her.", and the broader sad-lofi/late-night
     ambient niche). What actually differentiates the winners — aesthetic, character,
     titles, consistency, posting cadence, community?
   - Is there white space for a *recurring character with a narrative* (the girl as
     an implied story across videos/titles) vs. generic mood loops? Does character
     IP increase retention/loyalty/merch potential, or is it irrelevant to sleep viewers?

2. **What "product" maximizes the goal (revenue + durability).**
   - Sleep-loop wallpaper (max watch-time, low loyalty) vs. story-driven emotional
     content (higher loyalty/CTR, more effort) vs. a hybrid. Which has the better
     risk-adjusted ceiling for a solo operator with this pipeline?
   - Role of **Shorts/TikTok** as a top-of-funnel story engine feeding the long-form
     sleep catalog (CK has a 50+ hook library across curiosity/POV/bold/FOMO/comment-bait).

3. **The fleet architecture (2–5 channels).**
   - Should the channels be **sub-brands of one aesthetic universe** (same girl /
     same world, different moods/lanes) or **independent niches** (sleep, study,
     pet-calming, meditation)? Trade-offs for algorithm, cross-promotion, brand equity, risk.
   - Recommend a specific 3-channel slate with names, hooks, and why.

4. **Character & consistency as strategy.**
   - Given Soul ID makes a *locked, recognizable* character cheap: is leaning into a
     named, consistent persona (an IP you could extend to Spotify, merch, a "story")
     a real edge, or does it raise authenticity/disclosure risk? What do comparable
     AI-character channels show about ceiling and backlash?

5. **Emotional/psychological core.**
   - What is the actual *job-to-be-done* for the "young men who miss someone /
     can't sleep" audience? Companionship, catharsis, routine, parasocial comfort?
     Which content choices (voice/narration? spoken intros? recurring girl? lyrics
     vs instrumental?) deepen that without tipping into manipulative or risky territory?

6. **Differentiation levers we can actually pull** with this stack (Higgsfield
   motion + Soul ID + Suno + ffmpeg long-form): e.g., real cinematic motion (most
   competitors use static stills), a consistent character, story-titled series,
   seasonal/thematic drops. Rank them by impact-per-effort.

7. **Naming & expansion.** Is "2am without her." a channel or a *brand* that could
   parent a network (a "2am" universe: "2am without him.", "2am alone.", "3am
   thoughts.")? Recommend a naming/expansion system.

### Deliverable requested from the research instance
A concrete creative direction: (a) what the product *is* in one paragraph, (b) the
recommended 3-channel slate, (c) whether to lean into character-IP and how, (d) the
top 3 differentiation moves to execute first, (e) any policy/authenticity risks to
avoid. Tie recommendations back to the constraints in Parts 3–4 (credit budget,
Canada monetization, mid-roll posture, anti-inauthentic-content rule).

### Inputs the research instance should assume as fixed
- Pipeline & constraints in Parts 2–4 are settled; don't re-litigate tooling.
- Budget ceiling ~$100 CAD/mo; Higgsfield Plus is sufficient; Suno manual; VPS runtime.
- Human review gate stays. Organic growth only (no botting). YouTube-first, FB secondary.
