# Getting a YouTube refresh token — from your phone

The Python runs on a computer (your Chicago VPS or this environment). Only the
**Approve** tap happens on your phone. Do this **once per channel**; the token
lasts indefinitely.

## Part A — Google Cloud setup (all in a phone browser, ~10 min, one time)

1. console.cloud.google.com → create a project (e.g. "faceless-fleet").
2. APIs & Services → Library → enable **YouTube Data API v3**.
3. APIs & Services → OAuth consent screen → **External** → add your Google
   account as a **Test user** (keeps it in testing; no Google review needed).
4. APIs & Services → Credentials → Create credentials → **OAuth client ID**:
   - **Phone path (recommended):** type **Web application**; add Authorized
     redirect URI `http://<YOUR_VPS_IP>:8080/`
   - **Paste path:** type **Desktop app** (no redirect URI needed).
5. Download the client JSON → save it on the VPS as
   `faceless_fleet/secrets/client_secret.json`.

## Part B — mint the token (pick ONE)

### Option 1 — VPS redirect (cleanest, no copy-paste)
On the VPS:
```bash
python -m faceless_fleet.pipeline.upload 2am_without_her --auth \
    --redirect-host <YOUR_VPS_IP> --port 8080
```
It prints one link. Open it **on your phone**, tap **Approve** → Google
redirects back to the VPS, which prints `YT_2AM_REFRESH_TOKEN=...`.
(Open port 8080 on the VPS firewall for the duration.)

### Option 2 — manual paste (works anywhere)
```bash
python -m faceless_fleet.pipeline.upload 2am_without_her --auth --manual
```
Open the printed link on your phone, **Approve**, then copy the FULL URL it
redirects to (a "localhost" page that won't load — that's fine) and paste it
back at the prompt. It prints the token.

## Part C — store the token
- **VPS:** put `YT_2AM_REFRESH_TOKEN=...` in the cron environment / a `.env`.
- **GitHub Actions:** Settings → Secrets → Actions → add `YT_2AM_REFRESH_TOKEN`
  and `YT_CLIENT_SECRET_JSON` (paste the whole client_secret.json).

Repeat for each channel (the env var name is in each channel's YAML →
`oauth_secret_env`). Tip: one Google account can own multiple YouTube channels
(Brand Accounts) — switch channel during the Approve step to authorize each.
