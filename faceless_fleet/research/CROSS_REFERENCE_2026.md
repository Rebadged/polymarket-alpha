# Cross-reference: 2026 strategic validation vs. our build

Reconciles `2026_strategic_validation_canada.md` (a second model's cross-check of the
original `2026_fleet_research_dossier.pdf` against 2026 platform/regulatory reality)
against what we've actually built. Each item is tagged:

- **🔴 CHANGES BUILD** — we were wrong / a landmine; fixed or must fix.
- **🟡 DECISION** — CK should choose; affects look/budget/strategy.
- **🟢 CONFIRMS** — validates what we already do.
- **🔵 NEW LEVER** — opportunity we hadn't built (backlogged).

> Weighting rule still applies: this is *fleet/niche* research — back it over the old
> 2am experiment's character-specific data.

---

## API & uploads

**🔴 Hidden "Video Uploads/day" quota (HTTP 429).** `videos.insert` dropped 1,600 → ~100
units (Dec 2025), but a *separate, hidden* per-day Video-Uploads bucket caps **unverified**
API projects at ~**7–11 uploads/day** and throws 429 even with general-quota headroom.
Verified projects get 100/day.
→ **Done:** added `upload.max_uploads_per_day: 5` to `global.yaml`. The VPS cron / `weekly`
must honor it (our cadence is ~9 long-form/week across 3 channels ≈ 1.3/day, so we're safe,
but a same-day burst could trip it — keep channels staggered). **Action:** complete Google
project **verification + compliance audit** to lift the cap before scaling Shorts volume.
Also: `search.list` = 100 units; the pipeline must **never call search at runtime** (we
don't — titles are templated, not searched). 🟢

**🟢 Long-form = `stream_loop -c copy`.** Dossier independently prescribes the exact ffmpeg
stream-copy loop we already use (`loop_to_length`). Confirms the core. The dossier's
`-t 41400` (11.5h) hint ties to live streaming (below), not our VOD long-form.

## Audio, licensing & a second revenue stream

**🟡 DECISION — Suno music vs. pure CC0 ambience.** The dossier assumes a **Suno**-based
*music* pipeline; we currently plan **pure ambient SFX beds** (CC0 from Freesound). Key 2026
facts if we add Suno:
- Suno **Pro/Premier** = perpetual commercial license to monetize/distribute (you don't own
  the copyright; Suno does). Raw output is **not copyrightable** → can't enroll in Content ID
  → others can re-upload your tracks freely.
- Legacy models (V3.5/V4) deprecated; downloads disabled on free tier, capped on paid.
→ **Decision for CK:** (a) stay **pure ambience** (simplest, fully CC0/owned-process, no Suno
cost, but no music differentiation), or (b) add **Suno Pro** for soft musical beds under the
ambience (richer, but licensing/ownership caveats + $10/mo). This is the core of the
**audio deep-dive** (`RESEARCH_BACKLOG.md` #1).

**🟡 DECISION — loudness target.** We master to **−14 LUFS** (YouTube's normalization point —
correct for video). The dossier targets **−18 LUFS** for *Spotify/SOCAN-distributed* tracks.
These aren't contradictory: keep **−14 for YouTube**; if we distribute audio to streaming
(below), export a **separate −14-to-−18 master** for that channel. No change to the video
pipeline; note it for the distribution path.

**🔵 NEW LEVER — distribute the audio to Spotify/Apple for passive royalties.** Real but
constrained:
- DistroKid accepts AI audio (CD Baby/TuneCore reject it); must flag **Synthetic Content**
  per the **DDEX** standard or risk demonetization/strikes. Apple excludes fully-AI from top
  editorial playlists.
- Spotify functional-noise rules: track must hit **1,000 streams/12mo** to earn anything,
  be **≥2 min**, and noise streams pay **~20%** of a normal stream.
- **SOCAN (Canada):** *AI-assisted* (human authorship central, e.g. you re-arrange stems) =
  registrable for composition royalties; *fully AI-generated* = ineligible, and registering
  it as human work breaches membership. → Royalty collection requires real human editing.
→ Backlogged under audio + monetization. Modest upside; do it only after a channel works.

## Visual pipeline & inauthentic-content policy

**🟡 DECISION — locked camera vs. dossier's "add camera motion."** The dossier says a
*static image + audio loop* is no longer monetization-safe (2026 inauthentic sweep) and
pushes **camera motion + particle overlays + varied composition**. Important nuance: **we
are NOT static-image** — we animate via Kling (falling snow/rain/fire is real motion) and
rotate scenes/locations per upload, which already clears the bar the dossier is worried
about. **But** CK explicitly wants a **locked camera** (element-driven motion), which
conflicts with the dossier's "slow pans/dollies" suggestion.
→ **Recommendation:** keep the locked camera (it's the approved aesthetic AND the motion is
genuine, not a static slideshow), but **lean hard on the other two differentiators** the
dossier lists — (1) rotate scene/location every upload (already in `auto.py`), and (2) layer
**ffmpeg particle overlays** (drifting mist/sparks/extra rain) so no two videos are
pixel-similar. The `review.py` material-variation gate enforces it. CK: OK to stay
locked-camera + add overlay variation, or do you want occasional slow pans for safety?

**🔴 CHANGES BUILD — Higgsfield credit math was wrong.** We had `est_credits_per_clip: 8`.
Reality: Kling 3.0 720p ≈ **8.75 cr / 5s**, so our **10s** clips ≈ **17.5 cr**, and it takes
**~3 generations** to land one defect-free → effective ~**50 cr per usable 10s clip**.
→ **Done:** `global.yaml` now `est_credits_per_clip: 17` + `iteration_factor: 3`;
`batch_plan` reserves the iteration headroom so a budget can't over-plan. **Knock-on:** on
Plus (1,000 cr/mo) realistic throughput is ~**14–20 usable 10s clips/mo** fleet-wide — so
the "7 new clips/week" in `RESTOCK_SCHEDULE.md` is optimistic at 10s. Either **drop to 5s
master clips** (halves cost → 7/week fits) or **restock ~4/week**. Tied to the DECISION
above. The library + lossless looping means a modest clip count still feeds many videos.

## Growth levers (new)

**🔵 NEW LEVER — 24/7 live-stream loops for watch-hours.** The single biggest accelerator to
**4,000 watch-hours (YPP)**: restream a loop 24/7 via RTMP/OBS (0-sub channels CAN stream
from desktop; mobile needs 50 subs). **Hard rules:** restart the stream **every 11.5h** (под
12h → auto-archived as a public VOD that banks the watch-hours; **>18h → YouTube DELETES the
archive and erases all accumulated hours**). Sub-1,000 channels are capped at **40 concurrent
viewers**. → Backlog #3. A `deploy/live_loop.sh` (ffmpeg RTMP push + 11.5h restart cron) is a
clean future add once a channel + stream key exist.

**🔵 NEW LEVER — Facebook Creator Fast Track (Canada-eligible).** Cross-post watermark-free
9:16 Reels → guaranteed **$100–450/mo for 3 months** at 20k+ followers, then ongoing FCM ad
revenue. Pairs perfectly with the **Shorts funnel** (same vertical cuts). TikTok's program
**excludes Canada** — don't bother monetizing there. → Backlog #3/#4.

## Money & Canadian setup

**🔵 NEW LEVER / 🔴 must-do before monetization — W-8BEN.** File via AdSense **before**
monetizing: SIN on **Line 6** (Foreign TIN), claim **Article XII** of the Canada-US treaty →
**0% withholding** on royalties (vs default 30%). Miss it and YouTube withholds 30%.

**🟢 / note — GST/HST & structure.** Stay a **sole proprietor** (report on **T2125**) until
net profit is consistently **$80–100k**; incorporation overhead ($4–10k/yr) isn't worth it
below that. Watch the **$30k** small-supplier threshold — **zero-rated AdSense exports COUNT
toward it**; register for GST/HST once gross crosses $30k over a rolling 4 quarters (then you
can also recover ITCs on hardware/software/VPS). → Monetization doc (Backlog #4).

**🟢 Budget fits.** Dossier's stack — Higgsfield Plus (annualized ~$39) + (optional) Suno Pro
$10 + VPS ~$6 + DistroKid ~$2 ≈ **~$78 CAD/mo**, inside CK's ~$100 CAD ceiling. Our Hetzner
box is the VPS line. The credit-math fix above is what keeps generation inside the Higgsfield
line.

---

## Action summary

| # | Item | State |
|---|---|---|
| 1 | Upload daily cap (avoid hidden 429) | ✅ `max_uploads_per_day: 5` + verify project to scale |
| 2 | Higgsfield credit math (8→17 + iteration) | ✅ config + `batch_plan` fixed |
| 3 | Clip length 10s vs 5s (budget) | ✅ **CK: 5s** — `clip_seconds: 5`, `est: 9` |
| 4 | Locked camera vs add motion | ✅ **CK: keep essentially locked** (barely-perceptible drift max), motion on the scenery; particle overlays carry per-video variation |
| 5 | Audio: Suno music vs pure CC0 ambience | ✅ **CK: no Suno** — pure ambience now; deep-dive re-scoped to *safe audio now + custom/original audio long-term* |
| 6 | Particle-overlay variation step | ✅ built in `assemble.py` (`apply_particle_overlay`); drop CC0 overlays in `assets/overlays/<weather>.mov` to activate |
| 7 | 24/7 live-loop for watch-hours | 🔵 backlog → `deploy/live_loop.sh` (11.5h restart) |
| 8 | Shorts → Facebook Reels Fast Track | 🔵 backlog (Canada-eligible $) |
| 9 | W-8BEN + GST/HST + T2125 | 🔵 do before monetizing → monetization doc |

CK decisions #3–5 are **resolved** (2026-06). Particle-overlay step (#6) is now the primary
inauthentic-policy differentiator since the camera stays locked — build it into `assemble.py`
(layer a looping transparent rain/snow/spark element over the 5s unit before the lossless
loop, so it's encoded once and cheap). Remaining 🔵 items are backlogged.
