# Handoff: finish + smoke-test the unattended Cloud-API restock

**Who runs this:** a Claude Code web session that has `HIGGSFIELD_API_KEY` in its
environment (added after the env var was set, so it's actually injected). It runs every
command itself in its own sandbox — **the user is not at a PC and cannot run anything.**

**Goal:** confirm the Cloud-API path (`backend: rest`) authenticates and produces a clip,
fill in the two model slugs it needs, and report back. Code is already built + mock-tested
(`pipeline/rest.py`); only live values + a real call remain.

## What's already confirmed (no need to re-derive)

- SDK: `pip install higgsfield-client`; base URL `https://platform.higgsfield.ai`;
  auth header `Authorization: Key <cred>`.
- Credentials: SDK reads `HF_KEY` (single, may be `key:secret`) or `HF_API_KEY`+`HF_API_SECRET`.
  `rest.py::_ensure_key()` bridges our `HIGGSFIELD_API_KEY` → `HF_KEY` automatically.
- `subscribe(application, arguments)` POSTs `arguments` as JSON to `<base>/<application>`
  and polls to completion. `application` is the **model slug** (e.g. the known-good
  `bytedance/seedream/v4/text-to-image`).
- The MCP model names (`soul_2`, `kling3_0_turbo`) are a DIFFERENT namespace — they are
  NOT valid Cloud-API slugs. The slugs below must be read off the live API.

## Step 1 — verify the key is present (don't print it)

```bash
python -c "import os;k=os.environ.get('HIGGSFIELD_API_KEY');print('present,len',len(k)) if k else print('MISSING')"
pip install -q higgsfield-client
```

If MISSING, stop and tell the user the env var didn't inject (wrong environment, or the
session predates it).

## Step 2 — prove auth + the pipeline with a KNOWN-GOOD slug

Before hunting for the Higgsfield slugs, confirm the key + SDK + our wiring all work using
the one slug we already know is valid:

```python
import os; os.environ.setdefault("HF_KEY", os.environ["HIGGSFIELD_API_KEY"])
import higgsfield_client as hf
r = hf.subscribe("bytedance/seedream/v4/text-to-image",
                 arguments={"prompt":"a cozy snowy log cabin at night, warm windows",
                            "aspect_ratio":"16:9"})
print(r)   # expect an images[].url — this proves auth, billing, and result shape
```

- 200 + a URL → **auth works**, the whole `rest.py` flow is good; only the slugs are left.
- 401/403 → the key string or header is wrong (or it's a key:secret pair — set
  `HF_API_KEY`+`HF_API_SECRET` instead and retry). Report the exact status.
- If the sandbox blocks `platform.higgsfield.ai` (network policy), report that — it means
  the smoke test must run on the VPS, but the slugs can still be found via the dashboard.

## Step 3 — find Higgsfield's own image + image-to-video slugs

We want Higgsfield's stylized image model (Soul family) and a cheap image-to-video
animator (Kling Turbo family). Get the exact Cloud-API slugs by, in order of preference:
1. the model catalog / "Applications" list in the authenticated dashboard at
   https://cloud.higgsfield.ai (or its API docs), or
2. trying candidate slugs with the Step-2 snippet (swap the application string) until one
   returns 200, e.g. patterns like `higgsfield/soul-2/text-to-image`,
   `higgsfield/kling-3-turbo/image-to-video` (image-to-video takes an `image_url` arg).

Record the two that work.

## Step 4 — fill config + run ONE real clip

Put the confirmed slugs in `faceless_fleet/config/global.yaml`:

```yaml
generation:
  rest_image_model: "<confirmed image slug>"
  rest_video_model: "<confirmed image-to-video slug>"
```

Then the real end-to-end test (one clip, ~8 credits):

```bash
python -m faceless_fleet.pipeline.run restock-run rain_cabin --budget 8
```

Expected: it plans, generates a still, animates it, records the URL to
`restock/rain_cabin.json`, and downloads the MP4 to `assets/clips/rain_cabin/`. If the
sandbox can't download the CDN, the URL is still recorded + committable — that alone
proves generation; the VPS does the actual download via `restock-fetch`.

Check `balance` before/after to confirm the credit cost is sane (~8).

## Step 5 — report back (and commit)

- If it produced a clip (or a recorded URL): commit the config slugs + manifest
  (`git add faceless_fleet/config/global.yaml restock/ && git commit -m "Confirm Cloud-API
  model slugs + first REST restock" && git push`), and tell the user the unattended path
  is proven — they can flip `backend: rest` and uncomment the `restock-run` cron line.
- If blocked (auth or network), report the exact error + which step, so the issue is
  pinned (bad key vs wrong slug vs sandbox egress) without guessing.

Do NOT print the key value anywhere. Keep total spend to the ~8-credit single clip.
