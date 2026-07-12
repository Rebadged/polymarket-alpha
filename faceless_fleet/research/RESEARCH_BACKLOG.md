# Research backlog — open deep-dives for the Comforts fleet

What's already researched + built: **branding/visual identity** (see
`BRANDING_PLAYBOOK.md` + `BRANDING.md`), the **creative look**, **video format/structure**,
and the **pipeline**. The gaps below are the product-and-growth side. Each is scoped as a
brief so a deep-research session can run it and drop a cited report in `research/`, then
fold the actionable parts into the relevant doc (config/BRANDING/START_HERE/handoff).

> **Weighting rule:** back the *niche-level* research for this ambient fleet. The old
> "2am without her." channel was an experiment with idiosyncratic, character-specific data
> — **do NOT weight 2am-specific findings over fleet research.** (CK, 2026-06.)

---

## 1. Audio sourcing & licensing  — HIGHEST PRIORITY (the product + a risk landmine)

Audio is the star (people sleep/study to it). Current plan is thin (layer CC0 rain from
Freesound) and carries monetization risk. **CK decisions baked in (2026-06):** no Suno;
pure ambience for now. **Two-horizon framing CK raised — research BOTH:**
- **Now (safe audio):** the best *immediately usable, cleanly-licensed* sources for premium
  ambient beds, with the explicit caveat that popular CC0 files are **already used by many
  competitors** — so flag which sources are over-used and how to stay distinct.
- **Long-term (custom/original audio):** as the fleet scales it will **exhaust the good safe
  audio** and risk sounding like everyone else. So research a path to **custom/original
  ambient audio** for unlimited supply + a sonic signature: recording/field capture,
  procedural/generative ambient (non-Suno — e.g. granular/noise synthesis, dedicated SFX
  models), layering many CC0 elements into unique blends, or commissioned/licensed packs.
  Weigh cost vs differentiation vs the SOCAN human-authorship angle (custom = registrable).
Then also answer:
- **Best sources** for premium, **long, seamless, loopable** ambient at scale, ranked by
  quality + cost + license clarity: CC0 libraries (Freesound CC0, etc.), paid royalty-free
  libraries (Epidemic, Artlist, Storyblocks — do their licenses permit monetized YouTube +
  derivative loops?), AI audio generation (Stable Audio, ElevenLabs SFX, etc. — license to
  monetize? quality for sleep?), and field-recording packs.
- **Licensing for monetization**: what's safe to use on a monetized, *multi-channel* setup
  without Content ID claims/strikes; attribution mechanics; what to AVOID.
- **Music vs pure ambience** for each lane (does adding soft music help retention/RPM, or
  hurt the "pure rain" promise?), and how leaders handle it.
- **Upside — repurpose to streaming:** can the same loops be distributed as tracks to
  Spotify/Apple (DistroKid/etc.) for passive royalties? Rules, economics, gotchas.
- **Production specifics:** target length of source elements, how to get inaudible loops,
  mastering target (we use −14 LUFS / −1.5 dBTP / 6 LU — validate vs sleep-audio norms).
- **Deliverable:** a ranked sourcing recommendation + a licensing do/don't list → update
  each channel's `audio.sfx_library` plan and `deploy/` SFX-fetch step.

## 2. SEO & discoverability — the growth engine

- **Keyword demand vs competition** per focal point (cabin / campfire / tent) and per
  weather/season scene — which exact phrases have search volume and beatable competition.
- **Title/tag formulas that rank** in ambient (duration tags, "black screen", "no ads",
  "4K", scene + weather ordering). Validate/extend our `metadata.title_templates`.
- **Playlists, end screens, chapters, descriptions** — structure for session-binge +
  suggested-traffic. Playlist SEO specifically (ambient lives on playlists).
- **Traffic mix**: how much ambient comes from search vs suggested vs browse, and what
  that implies for packaging.
- **Deliverable:** per-channel keyword/title kit → update `metadata` blocks + a titling
  guide for the review gate.

## 3. Growth & algorithm cold-start

- **24/7 live-stream loops** — do ambient channels bootstrap with always-on live? Mechanics
  (restream a loop), algorithm/discovery benefit, moderation/cost, risk. Could the pipeline
  feed a live loop?
- **Shorts funnel** — vertical 15–30s cuts of the scene clips with a hook → drive subs to
  long-form. (Half-designed already; finish if research supports it.)
- **Cold-start playbook** — realistic path to YPP (1,000 subs + 4,000 watch-hours) for a
  brand-new faceless ambient channel: cadence, first-30-videos strategy, cross-linking the
  sister channels, external seeding.
- **Deliverable:** a launch-and-grow playbook → update `START_HERE.md` + cadence config;
  decision on live + Shorts.

## 4. Monetization stack + Canadian operator setup

- **YPP path + RPM levers** for ambient (8-min midroll threshold, ad placement, audience
  geography toward US/UK/CA/AU).
- **Secondary revenue**: streaming distribution (from #1), affiliates (sleep products),
  sponsorships (Calm/Headspace-type, the $16–20 CPM wellness buyers), memberships.
- **Canadian practicalities**: AdSense setup, **W-8BEN tax treaty** so YouTube withholds at
  the treaty rate (not flat 30%), GST/business considerations, one-account-many-channels vs
  separate AdSense risk.
- **Deliverable:** a monetization checklist + the tax/AdSense setup steps → `START_HERE.md`.

---

### Partially answered already
A second-model 2026 validation dossier (`2026_strategic_validation_canada.md` +
`2026_fleet_research_dossier.pdf`, reconciled in `CROSS_REFERENCE_2026.md`) already covers
chunks of #1 (Suno/DDEX/SOCAN licensing, Spotify functional-noise rules), #3 (24/7 live
loops, Facebook Reels Fast Track), and #4 (W-8BEN, GST/HST, sole-prop-vs-incorp). The deep
dives should EXTEND these (sourcing/quality specifics, keyword data, exact cold-start
playbook), not re-derive them.

### Not gaps (already handled)
Pipeline/automation, the inauthentic-content compliance checklist (`BRANDING.md`), account
hygiene (separate Brand Accounts), loudness/loop policy, the restock + weekly automation,
the corrected Higgsfield credit math + hidden upload cap (`CROSS_REFERENCE_2026.md`).
