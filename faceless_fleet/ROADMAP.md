# Faceless Fleet — Consolidated Strategy & Roadmap

> Single source of truth, folding in all three research rounds (channel expansion,
> creative/product brief, geography/RPM). Operator: **CK** (Canada, solo). Engine:
> **YouTube**; secondary: **Facebook Reels**. Budget: **~$100 CAD/mo**. Pipeline,
> tooling, and the human review gate are settled (see README); this is the *plan*.

## The product, in one paragraph

A fleet of **faceless, no-character, no-narration ambient channels** segmented by
**use-case/mood** (not by geography, not by character). The watch-time engine is a
long-form catalog (1/3/8-hour seamless loops); the discovery engine is a Shorts/
Reels funnel built from CK's 50+ hook library ("Hybrid Discovery-to-Catalog"). The
durable moat is **real cinematic motion** (Higgsfield) over the static-image
incumbents — which simultaneously raises quality, lifts retention, and supplies the
per-video variation YouTube's inauthentic-content rule demands. Revenue is a
modest-RPM, high-watch-hours play concentrated in **Tier-1 English markets**,
captured during the **Q4 CPM premium**.

## The slate (3 channels — use-case segmented)

| # | Channel (config) | Lane | Why | Status |
|---|------------------|------|-----|--------|
| 1 (lead) | `rain_cabin` | Rain/Storm + Cozy Cabin | Biggest evergreen demand × motion moat × broad JTBD | built; content pending |
| 2 | `sleep_ambient` | Sleep / Ambient Music | Largest audience; pure overnight watch-time; original Suno music | built |
| 3 | `pet_calming_dogs` | Pet-Calming (dog) | Less saturated, sticky, DAYTIME occasion → smooths fleet revenue | built |

Deferred: meditation/sleep-story narration (transformative hedge if a music channel
is flagged); lo-fi study (Channel 4 later). The `2am without her.` character concept
is archived (`config/channels/_archive/`).

## Ad configuration by content type (research table)

| Content | Length | Pre-roll | Mid-rolls | Post-roll |
|---------|--------|----------|-----------|-----------|
| Deep-sleep / rain-for-sleep | 1–8 h | On | **Off** | **Off** (post-roll at end of a sleep journey = #1 complaint) |
| Study/focus cut | 30–60 min | On | Sparse (~12–15 min, at transitions) | Optional |
| Pet-calming | 1–8 h | On | Sparse (~15 min) | Off |
| Shorts | <60 s | Shorts ad pool | n/a | n/a |

Encoded per channel in each YAML `ads:` block. (Mid-roll *placement* is set in YouTube
Studio, not fully via API — set it there per channel.)

## Retention playbook (ranked, all built into the pipeline)

1. **Seamless looping** — wrap-crossfade so the seam is invisible across hours (`assemble.make_seamless_*`). ✅
2. **First-30s confirms the thumbnail/title promise** (rain you can hear, fire you can see). 
3. **Playlists + autoplay** — intent playlists ("Rain for Deep Sleep", "8-Hour Storms") chain the night, stacking impressions + session-contribution signal.
4. **End-screen self-loops** to the next video.
5. **Audio consistency** — −14 LUFS loudnorm, no spikes that wake sleepers. ✅
6. **Length ladder** (1/3/8 h) — one production captures multiple intents. ✅
7. **Title/thumbnail template + SEO** — generic keyword first, location seasoning.

## Geography & RPM (settled — research round 3)

- **RPM = viewer country, driven by the LANGUAGE of your metadata.** Not your
  residence, not the depicted location. → Target **Tier-1 English** (US > UK/CA/AU)
  via English titles/tags and North-American-evening upload timing.
- **Canadian-content regulation (Bill C-11) is a dead end** for UGC creators — no
  discoverability or RPM lever; thresholds (CA$10M/$25M) are irrelevant; UGC ad
  revenue is carved out. Don't pursue it. (CMF Digital Creators grant: $20k/75%, but
  needs incorporation + an eligible genre; faceless ambient doesn't fit — low priority.)
- **Don't build per-geography channels.** Rotate **short named locations *within***
  each channel as per-video variation + SEO seasoning (`location_pool` in `rain_cabin`).
  Title convention: `[Sound + Benefit] | [short Location] | [Duration] [+ modifier]`.
- **Modifiers** reflect OUR edge: "Cinematic", "Crackling Fireplace", "No Mid-Roll Ads".
  Never "Black Screen" (we're the opposite) or "No Ads" (we run pre-roll).
- **Seasonality:** weight cozy/winter uploads to NH **autumn–winter**; **front-load
  high-effort uploads into early October** to bank ranking signal before the Q4 CPM
  premium (30–70% above average). Treat January (CPM crater) as batch/evergreen month.
  Optional light AU counter-season (May–Aug). 

## Canadian operator hygiene (do once)

- **AdSense W-8BEN** — file it, use your **SIN as foreign TIN** → **0% US withholding**
  (vs up to 24–30% without). 
- Income = self-employment → **T2125**; register **GST/HST** once revenue > **CA$30k**
  over four consecutive quarters (consider the Quick Method).
- **Facebook Content Monetization is available in Canada** — stand up FB pages, cross-post
  Reels (3+ min where possible for in-stream ads) toward the ~10k-follower threshold.
- TikTok/IG = reach only (TikTok Creator Rewards excludes Canada).
- *(Not tax advice — confirm with a Canadian accountant.)*

## Multi-channel hygiene (avoid domino bans)

Each channel = a **separate Brand Account, ideally separate Google accounts/emails**
(`oauth_secret_env` per channel already supports this). No cross-channel duplicate
uploads (similarity detection flags networks). The VPS does downloads/assembly only;
uploads go through each channel's own YouTube API creds. Organic only — no botting.

## Staged roadmap

**Stage 1 (Mo 1–3): prove the funnel on Channel 1 (`rain_cabin`).**
2–3 distinct long-form/week (1/3/8-h ladder) + 4–5 Shorts/week from the hook library.
Ads: pre-roll on, mid/post-roll off. Goal: **1,000 subs (via Shorts) + 4,000 watch-hours
(via long-form autoplay) → YPP.**
- *Advance when:* YPP accepted + 1 month stable (non-flagged) monetization. If rejected
  for inauthentic/reused content → increase per-video variation before scaling.

**Stage 2 (Mo 3–6): add Channels 2 & 3** under separate Brand Accounts/emails; stand up
Facebook pages + Reels cross-posting toward ~10k followers.
- *Advance when:* Channel 1 stable + 90 days strike-free; each new channel clears its own YPP.

**Stage 3 (Mo 6–12): optimize ad load empirically + consider Channel 4.**
A/B sparse mid-rolls vs none on study/focus cuts (compare AVD + revenue/session).
- *Thresholds that change the plan:* mid-rolls drop AVD >5 pts → pre-roll only;
  sleep RPM ~ $1–3 not ~$10 → double down on watch-hours + FB Reels;
  a music channel flagged → pivot it to a narration/sleep-story layer (transformative hedge).

## Build status (this repo)

**Done:** pipeline (generate→assemble→review→upload); 3-channel slate; seamless loop
+ −14 LUFS; ad-config; rotating short/long locations; jittered scheduling; phone OAuth
helper; VPS deploy scripts + fetch/assemble; GitHub Actions upload workflow.
**Validated:** 3-h render in ~60s; audio normalized to −14.1 LUFS; real Higgsfield
generation (still + motion clip) proven earlier.
**Pending (CK/human):** create channels (Brand Accounts + emails); YouTube OAuth per
channel; Suno beds (manual); run first full assembly on the VPS; then drip-publish.
