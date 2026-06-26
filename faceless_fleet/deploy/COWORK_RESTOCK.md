# Weekly clip restock — the one step that needs an agent

`weekly` publishes from the clip library. It does **not** make new clips. Generating
clips needs Higgsfield, which can't run on plain cron without an API key — so this is
the single human-or-agent step in the whole fleet. Two ways to do it:

- **A — Cowork / Claude (today, no API key):** paste the prompt below. The agent runs
  `batch-plan`, then generates + downloads each clip in the manifest, within budget.
- **B — Unattended (needs `HIGGSFIELD_API_KEY`):** set `generation.backend: rest` in
  `config/global.yaml` and run `batch-plan` then the REST fulfiller on cron. No agent.

You only need to restock when a channel is running low on fresh clips. The loop reuses
clips (LRU — least-recently-used first), so a library of ~8–12 per channel lasts weeks.

---

## The paste-able Cowork prompt (option A)

> You are restocking the ambient-YouTube clip library. Work inside the repo at the path
> I give you. Do this for the channel slug I name (e.g. `rain_cabin`, `campfire`,
> `camping_tent`):
>
> 1. Run: `python -m faceless_fleet.pipeline.run batch-plan <slug> --budget 160`
>    This writes `assets/clips/<slug>/_to_generate.json` — a list of clips to make,
>    already capped to the budget. Read that file.
> 2. For **each item** in `items`, using the Higgsfield MCP tools:
>    a. `generate_image` with `model = item.image_model`, `prompt = item.still_prompt`,
>       `aspect_ratio = item.aspect_ratio`. Wait for it, then `job_display` so I can see it.
>    b. `generate_video` with `model = item.video_model`, the still as the input image,
>       `prompt = item.motion_prompt`, `duration = item.duration`. Keep the camera locked
>       (no pan/zoom) — only the named motion (snow, rain, flicker) should move.
>    c. Download the finished MP4 to `assets/clips/<slug>/<item.clip_name>` (exactly that
>       filename — the loop matches on the `scene__location` stem).
> 3. Stop when the manifest is fulfilled or the budget is spent. Tell me how many clips
>    you made and the credits used (`balance` before/after). Do NOT exceed the budget.
>
> Notes: stylized painterly-cozy look, not photoreal. Audio is handled separately — you
> are only making silent video clips. If a download is blocked by sandbox egress, save
> the Higgsfield media IDs and tell me; I'll pull them on my PC.

---

## What `batch-plan` decides for you

- **What's missing:** it diffs `scene_pool × location_pool` against the clips already in
  `assets/clips/<slug>/`, so it never re-makes one you have.
- **How many:** `floor(budget ÷ est_credits_per_clip)` (default 160 ÷ 8 = 20 clips max).
- **The prompts:** it expands each scene's `still_prompt` / `motion_prompt` with the
  channel's locked look tokens + the location, and appends the negative prompt. The agent
  doesn't write prompts — it just executes the manifest. That keeps the look consistent
  and the token spend predictable.

## After restocking

Nothing else to do. The next `weekly` cron run automatically picks up the new clips
(it globs the folder fresh each run). The library and the publish loop are decoupled on
purpose: restock occasionally, publish forever.
