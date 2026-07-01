# Fable 5 handoff — image generation + project review

You're joining an in-flight project: a fleet of **faceless ambient-YouTube channels**
("Cabin/Campfire/Tent Comforts") — cozy looping sleep/study videos, fully automated. A
Cowork session is **actively shipping** (branding + first content), so coordinate: your
two jobs are **(1) generate on-brand imagery** (you may be better at it) and **(2) a general
review** of the project. Don't refactor things Cowork is mid-build on; keep changes small,
committed clearly, and flag rather than rewrite.

**Orient first (5 min):** read `WHATS_WHERE.md` (map + changelog), `COWORK_HANDOFF.md`
(mission + playbook), `research/CROSS_REFERENCE_2026.md` (resolved decisions + corrected
math), `BRANDING.md` (brand/thumbnail system). Branch: `claude/faceless-ai-youtube-channels-74t0he`.

---

## Job 1 — Image generation (the locked look; do NOT drift)

Generate via the **Higgsfield MCP** (`generate_image`, model **`soul_2`**; preview with
`job_display`). What to make: **scene stills** (the base frame each 5s clip animates from),
plus **branding** (avatars/banners) for any channel that still needs them.

**The look (identical across the fleet — this is the brand):**
- **Cinematic stylized painterly realism, idealized cozy** — NOT photoreal, NOT cartoon.
  Warm focal glow vs cool night, shallow depth of field, subtle film grain, 16:9.
- **Composition:** the focal point (cabin / campfire / tent) sits in an **open clearing**
  with a **DENSE forest as a backdrop *behind* it**. Warm firelight/lantern flicker
  reflecting on snow/ground.
- **Hard no's (CK rejected these repeatedly):** **no foreground tree trunks / no dark
  vertical trunks framing the shot / no bark in the foreground / nothing crowding the
  focal point.** Also: no people, no text/letters (AI renders them as gibberish), no
  clutter, minimal objects, no warped/melting geometry, no watermarks/logos.

**Where the exact prompts live — use them, don't invent:**
- `config/channels/<slug>.yaml` → `scene_pool[].still_prompt` / `motion_prompt`, with
  `{film_look}` / `{motion_principle}` / location tokens. `pipeline/generate.py`
  (`_tokens`, `_fmt`) shows how they expand; each channel's `identity.negative` is the
  negative prompt — **always append it.**
- Branding prompts + specs (avatar 2048², banner 2048×1152→upscale to 2560×1440, no baked
  text) are in `BRANDING.md` → "Thumbnail & brand system".

**Aspect ratios:** long-form stills **16:9**; Shorts **9:16**; avatar **1:1**; banner 16:9.

**Iterate for clean geometry:** expect ~**3 attempts** to get one free of AI defects
(warped logs, melted edges). Generate, `job_display`, pick the clean one. Images are
cheap (~0.1 cr); the cost is in video, so iterating stills freely is fine.

**Getting results out (egress caveat):** if you're in a **sandbox** (Claude Code web) you
**cannot download** Higgsfield's CDN (`403 CONNECT`) — instead record the URL via
`python -m faceless_fleet.pipeline.run restock-record <slug> <clip_name> --video-url <URL>`
(for clips) or just hand CK the `job_display` previews to download from his library. If
you're running **on CK's PC / in Cowork**, you can download normally into
`assets/clips/<slug>/` (stills) — the pipeline animates + assembles from there.

**Decisions already made (don't relitigate):** 5s master clips; camera essentially locked
(motion is the falling snow/rain/fire, not the camera); no Suno; particle overlays carry
per-video variation. See `CROSS_REFERENCE_2026.md`.

---

## Job 2 — General project review

Do a real review, not a rubber-stamp. Produce a **findings list** (bug / inconsistency /
risk / suggestion, each with file:line and a concrete fix). Focus on:

- **Pipeline correctness** (`pipeline/*.py`): the ffmpeg chain in `assemble.py` (seamless
  loop, SFX bed, loudnorm, the new `apply_particle_overlay`), `weekly.py` +
  `restock.py`/`rest.py` flow, `upload.py` quota handling, `batch_plan.py` budget math.
- **Config ↔ code consistency**: do the channel YAMLs provide every field the code reads
  (scene ids, `audio_layers`, `season_audio`, `oauth_secret_env`, `cadence`)? Any drift
  between `global.yaml` and what modules expect?
- **Docs ↔ reality**: does `WHATS_WHERE.md` / `START_HERE.md` / `CROSS_REFERENCE_2026.md`
  match the actual code + resolved decisions?
- **Compliance coverage**: is the material-variation story real (scene rotation + overlay +
  audio/season + title), given the 2026 inauthentic-content rule? Gaps?
- **Correctness of the 2026 corrections**: credit math (`est_credits_per_clip: 9` +
  iteration), the hidden `max_uploads_per_day: 5` cap — are they actually honored in the
  code paths that upload/plan?
- **Security**: confirm no secrets are committed (keys/tokens/`client_secret*.json` are
  gitignored); flag anything that could leak.

Deliver findings as a list CK can act on (or open small, clearly-scoped commits for
obvious fixes — but coordinate with Cowork so you don't collide on the same files).

---

## Guardrails
- **Look consistency** is the brand — match the spec above exactly; when unsure, prefer
  CK's approved reference (`047a7022`, the Cabin snowy exterior) over improvising.
- **Credit discipline:** iterate stills freely (cheap); be sparing with video (~8.75 cr/5s
  + iteration). Don't launch large batches without CK's ok.
- **Security:** never put keys/tokens/passwords in chat or git.
- **Coordinate with Cowork:** it's actively building; your review is mostly read + flag.
  Small, isolated commits only; note what you touched so work doesn't collide.

## What's pending (so you know where you fit)
Channels being created + branded (Cowork); first clip libraries + SFX (`assets/sfx/`) +
overlays (`assets/overlays/`) not yet added; YouTube OAuth + first upload; Cloud-API slugs
unconfirmed (`deploy/probe_slugs.py`); VPS not yet set up; deep-dives open
(`research/RESEARCH_BACKLOG.md`: audio, SEO, growth/live/Shorts, monetization+CA tax).
Your imagery feeds the clip libraries; your review de-risks the whole thing before scale.
