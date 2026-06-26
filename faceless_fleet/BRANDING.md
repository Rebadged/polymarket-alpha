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
