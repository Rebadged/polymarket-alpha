# Connecting "Cabin Comforts" to the pipeline (from scratch)

You have no Google Cloud account yet — that's fine, it's free and takes ~15 min.
The goal: a **refresh token** scoped to "upload videos," stored as a **secret** on
your VPS. Never paste passwords or the token into chat.

> ⚠️ THE #1 GOTCHA (read first): an OAuth app left in **"Testing"** mode issues
> refresh tokens that **die after 7 days**. To get a token that lasts, set the
> consent screen's **Publishing status to "In production"** (Part B, step 5). The
> `youtube.upload` scope is "sensitive," not "restricted," so for your *own*
> account you can publish to production WITHOUT Google verification — you'll just
> click through an "unverified app" warning once. This makes the token permanent.

---

## Part A — Google account + the channel (phone is fine)

1. Create a **new Gmail** dedicated to this channel (fleet hygiene = one email per
   channel so one strike can't cascade). e.g. `cabincomforts.yt@gmail.com`.
2. On YouTube (signed in as that account) → create the channel. Use a **Brand
   Account** (YouTube Studio → Settings → Add/Manage channels) named **Cabin Comforts**.
3. **Verify the channel by phone**: youtube.com/verify — REQUIRED, or uploads via
   API return 403.
4. Customize → upload the **avatar** + **banner** (download them from Higgsfield),
   paste the **bio**.

## Part B — Google Cloud project + OAuth client (phone-browser OK)

Sign in to **console.cloud.google.com with the SAME Google account** that owns the channel.

1. Accept the terms on first visit. (No billing/credit card needed — YouTube Data
   API v3 is free within quota.)
2. Top bar → project dropdown → **New Project** → name `cabin-comforts` → Create.
   Make sure it's the selected project.
3. **APIs & Services → Library** → search **"YouTube Data API v3"** → **Enable**.
4. **APIs & Services → OAuth consent screen**:
   - User Type: **External** → Create.
   - App name: `Cabin Comforts Uploader`; user support email + developer email: your email → Save and continue.
   - Scopes: skip (Save and continue) — the code requests the scope itself.
   - Test users: add your channel's Google account email → Save and continue.
5. **Publish the app** (this is the token-longevity fix): on the OAuth consent
   screen, set **Publishing status → "In production"** → confirm. (You can ignore
   verification; sensitive scope + own account is allowed. During login you'll see
   "Google hasn't verified this app" → **Advanced → Go to Cabin Comforts Uploader
   (unsafe)** → continue. "Unsafe" just means unverified — it's your own app.)
6. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Desktop app**; name `Cabin Comforts Desktop` → Create.
   - **Download JSON** → this file is your `client_secret.json`.

## Part C — mint the refresh token (at your computer / the VPS)

On the VPS (where the repo is checked out and uploads will run):

```bash
mkdir -p faceless_fleet/secrets
# put the downloaded client_secret.json here:
#   faceless_fleet/secrets/client_secret.json
pip install -r faceless_fleet/requirements.txt

# phone-friendly: approve on your phone, paste the redirected URL back
python -m faceless_fleet.pipeline.upload rain_cabin --auth --manual
```

It prints a link → open on your phone → approve (click through the "unverified"
warning) → copy the redirected URL → paste it back → it prints:

```
YT_RAINCABIN_REFRESH_TOKEN=1//0a...your-token...
```

## Part D — store the secret (NOT in chat)

On the VPS, add to the cron/service environment (e.g. an `.env` the scripts load,
or the crontab env), alongside the client secret path:

```
YT_RAINCABIN_REFRESH_TOKEN=1//0a...   # the token from Part C
```

Keep `faceless_fleet/secrets/client_secret.json` on the VPS only (it's gitignored).
Backup path: store both as **GitHub → Settings → Secrets → Actions**
(`YT_RAINCABIN_REFRESH_TOKEN`, `YT_CLIENT_SECRET_JSON`) if you ever upload from CI.

## Part E — tell me "connected"

Once the token's in place, I drive it: `upload rain_cabin` publishes (private +
jittered publishAt). Test first with `--dry-run` (no real upload), then live.

---

### Quick reference — what's secret vs not
| Item | Sensitive? | Where it lives |
|---|---|---|
| Google password | YES | only you, never shared |
| `client_secret.json` | mild | VPS `secrets/` (gitignored) |
| **refresh token** | YES | VPS env var / GitHub secret — never chat |
| client ID, project name | no | fine to mention |
