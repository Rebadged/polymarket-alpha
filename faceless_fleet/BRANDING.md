# Fleet branding

Every "Comforts" channel gets the same treatment so they read as a family.

## Assets per channel

| Asset | Spec | Source |
|-------|------|--------|
| **Avatar** (profile pic) | square, 2048×2048 → YouTube uses 800×800, shown in a **circle** | Higgsfield (iconic focal point, centered so it survives the circle crop) |
| **Banner** (channel art) | **2048×1152** exactly (YouTube's size; safe area is the center ~1546×423) | Higgsfield (wide focal-point panorama, subject near center) |

Same stylized painterly-cozy look as the videos; **no text baked in** (AI renders
text as gibberish) — the channel name shows beside the avatar on YouTube anyway.

## Optional: name on the banner

If you want the channel name on the banner, it's added crisply with a real font
(not AI) for a consistent family look — done with a small overlay step (Pillow/
ffmpeg on the VPS, or Canva). Ask and I'll wire it; otherwise scenic-only is clean.

## Generated so far

- **Cabin Comforts** — avatar + banner done (earlier this build).
- **Campfire Comforts** — avatar + banner generated (review).
- **Tent Comforts** — avatar + banner generated (review).

(All live in your Higgsfield library; download the ones you pick.)

## Uploading (one-time per channel, ~2 min)

YouTube Studio → **Customization → Branding**:
- **Picture** ← the avatar (this one is Studio-only; no API exists for profile pics)
- **Banner image** ← the banner
- **Video watermark** ← optional, reuse the avatar

Then **Customization → Layout / Basic info** to set the bio + the **Featured
channels** section linking the sister "Comforts" channels (cross-discovery).

## Why this isn't in the automated loop

Branding is a **one-time channel setup**, not per-video — so the recurring
`auto` loop stays fully hands-off. We just generate the assets once per new
channel and you drop them into Studio when you create it.

---

## Thumbnail & brand system (distilled from research/BRANDING_PLAYBOOK.md)

The full playbook is in `research/BRANDING_PLAYBOOK.md`. Here are the rules that
actually apply to our 3 focal-point Comforts channels — follow these when making
avatars, banners, and thumbnails.

### Locked variables (recognition without a face)
A faceless channel needs four things consistent, forever:
1. **One color grade** per channel (warm focal glow vs cool night — already in each
   channel's `identity.palette`).
2. **One font** for every wordmark/overlay — a bold condensed sans that survives at
   phone size: **Bebas Neue, Anton, Oswald Bold, or Montserrat ExtraBold**. Pick one
   for the whole fleet (family consistency) or one per channel; never mix per-video.
3. **A repeatable thumbnail template** (2–3 per channel, used for ~80% of uploads).
4. **An avatar that is an OBJECT/glyph**, not a scene — it must read at **98px in a
   circle**: Cabin = a warm rain-streaked window or single flame; Campfire = the fire;
   Tent = the glowing tent. Centered, high-contrast, one bright blob.

### Thumbnails (the brand IS the thumbnail)
- **Spec:** 1280×720, <2 MB. Make these as a real compositing step (Pillow/ffmpeg/Canva)
  from the scene still — NOT an AI render with baked text (AI text = gibberish).
- **Image-forward, ONE utility tag.** Ambient has no curiosity gap; sell *escapism +
  utility*. The image creates "I want to be in there"; add **one** fixed tag that
  declares format/utility, not mood: **"10 HOURS", "RAIN & THUNDER", "BLACK SCREEN".**
  ≤3 words / ~12 chars, bold condensed font, **bottom-left or top-left** — never
  bottom-right (YouTube's duration badge sits there).
- **Warm/cool contrast** = the recognition signature; the focal glow must read as a
  single bright blob at thumbnail size. Avoid busy interiors (mud on mobile).
- **60-30-10 color:** ~60% background, ~30% scene/subject, ~10% accent (the tag).

### Banner & avatar specs (2025–2026)
- **Banner:** generate/upload **2560×1440** (Higgsfield outputs 2048×1152 — upscale, or
  it's the accepted minimum). Keep the focal subject + any wordmark inside the **center
  1546×423 safe area** (design wordmark to the tighter **1235×338**), and leave the
  **bottom-left clear** (the avatar overlaps it). No baked-in AI text.
- **Avatar:** 800×800, renders as a circle as small as 98px. Object/glyph, centered.
- **Wordmark:** lowercase channel name in the chosen font, added crisply with a real font
  (Pillow/Canva), inside the banner safe area — matches the avatar's style.

### Compliance: the material-variation checklist (inauthentic-content rule)
YouTube's July-2025 "inauthentic content" rule demonetizes channels whose videos have
"little to no variation." Keep the **frame** consistent (font, palette, composition,
avatar — all explicitly allowed) but make every video **materially distinct**. The human
review gate (`review.py`) should enforce, per upload:
- Distinct **scene** (different weather/season/location, not a swapped word)?
- Distinct **audio mix** (different focal + seasonal palette)?
- **Non-duplicative title**?
If two uploads could be confused for each other, one fails. Our Higgsfield-original
footage + original audio already clears the *reused-content* bar (near-zero third-party
copyright) — this checklist covers the *inauthentic* bar. (`policy.require_distinct_from_last`
in config is the automated half of this.)

### Per-channel quick spec
| Channel | Focal motif (avatar) | Grade | Lead utility tag |
|---|---|---|---|
| **Cabin Comforts** | warm rain-streaked window / flame | storm-blue + firelight amber | "RAIN & THUNDER" / "10 HOURS" |
| **Campfire Comforts** | the campfire | deep-blue night + fire amber | "CRACKLING FIRE" / "10 HOURS" |
| **Tent Comforts** | the glowing tent | night blue + lantern gold | "RAIN ON TENT" / "10 HOURS" |

Distinctiveness check: the three must not look like each other — they differ by focal
motif and exact grade, but share the "Comforts" family system so cross-linked viewers
recognize them as siblings.
