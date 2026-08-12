# Restock on a schedule — the weekly Claude session

You wanted restock to run itself, the same way the Sunday publish cron does — "create
~7 clips a week, Sunday it restocks." This is how. Restock is the one step that needs an
agent (Higgsfield is MCP-only on your plan), so it runs as a **weekly Claude scheduled
session**, and a tiny git-based bridge carries the clips to your VPS.

## The weekly rhythm

```
SUN 03:00  Claude scheduled session (the web "Schedule" trigger)
           └─ for each channel: batch-plan → generate clips via Higgsfield
              → restock-record the URLs → commit & push  restock/<slug>.json
                         │  (only URLs travel through git — no video bytes)
                         ▼
SUN 03:30  VPS `weekly` cron (already in crontab.example)
           └─ git pull → restock-fetch downloads the new clips into
              assets/clips/<slug>/ → publishes the week (private + jittered)
```

The 30-minute gap lets the session finish and push before the VPS pulls. `restock-fetch`
is idempotent and folded into `weekly`, so the VPS side is fully automatic — you only set
up the schedule once.

## Step 1 — set up the weekly Claude session (one time, ~2 min)

`CronCreate` inside a chat won't work for this: those jobs die with the session and expire
after 7 days. The durable, nobody-present scheduler is the **Schedule** feature in Claude
Code on the web — it launches a *fresh* session on a cron. Docs:
https://code.claude.com/docs/en/claude-code-on-the-web

Create a schedule with:

- **Cron:** `7 3 * * 0`  (Sunday 03:07 — a few minutes before the VPS publish run; the
  off-:00 minute is deliberate so it doesn't pile onto the hour)
- **Repo / branch:** this repo, your working branch
- **Prompt:** paste the block below verbatim.

> **Weekly restock.** For each channel in `rain_cabin`, `campfire`, `camping_tent`,
> restock its clip library — but stop once you've generated **7 new clips total across the
> whole fleet** (≈56 Higgsfield credits). Spend the budget on whichever channels are
> lowest on clips first.
>
> For each channel:
> 1. `python -m faceless_fleet.pipeline.run batch-plan <slug> --budget 56` and read
>    `assets/clips/<slug>/_to_generate.json`.
> 2. For each item (until the fleet-wide total hits 7): `generate_image` (model =
>    `item.image_model`, `prompt = item.still_prompt`, `aspect_ratio = item.aspect_ratio`);
>    then `generate_video` (model = `item.video_model`, the still as input, `prompt =
>    item.motion_prompt`, `duration = item.duration`, camera LOCKED). Stylized cozy look.
> 3. Get the finished video's URL from the generation result and run:
>    `python -m faceless_fleet.pipeline.run restock-record <slug> <item.clip_name> --video-url <URL> --image-url <still_URL>`
> 4. After all channels: `git add restock/ && git commit -m "Weekly restock <date>" && git push`.
>
> Then check `balance` and report how many clips you made and credits used. Never exceed
> 7 clips / ~56 credits. Do not assemble or upload — the VPS handles that.

That's it. From then on it self-runs every Sunday; you just glance at the session summary
if you want to.

## Step 2 — confirm the VPS side (already done)

`crontab.example` runs `weekly` Sunday 03:30. `weekly` now calls `restock-fetch` per
channel first, so the new clips land in the library before publishing. Make sure the VPS
cron does a `git pull` at the top of the job (the example includes it) so it sees the
manifests the session just pushed.

## Budget / volume

- Default is **7 clips/week fleet-wide** (~56 credits ≈ ~224/month — comfortable on Plus).
  Change the number in the prompt to go faster or slower.
- `batch-plan` only ever lists clips you don't already have, so you never pay to
  regenerate, and a healthy library (~8–12/channel) means most weeks add just a few.

## If a URL ever expires before the VPS pulls

`restock-fetch` logs the failure and skips it; the channel just publishes from its
existing library that week (no crash). The 30-minute gap makes this rare. If you'd rather
remove the gap entirely, the alternative is the **fully unattended VPS path**: put a
`HIGGSFIELD_API_KEY` on the box, set `generation.backend: rest`, and a single cron line
generates + publishes with no Claude session at all — see the commented block in
`crontab.example`. Use that if you get API access; otherwise the scheduled-session path
above is the MCP-only way and works today.
