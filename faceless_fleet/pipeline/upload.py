"""Stage 4 — YouTube upload with scheduled (private + publishAt) release.

Uploads everything in output/approved/<slug>/ as PRIVATE with a jittered
publishAt; YouTube flips each one public automatically. Resumable upload with
exponential backoff on 5xx, per the official Google sample.

AUTH: OAuth2 "Desktop app" credential. Store the long-lived REFRESH TOKEN per
channel (access tokens self-regenerate). The refresh token for each channel goes
in the env var named by that channel's `oauth_secret_env` (see its YAML).

  Client secret JSON ->  faceless_fleet/secrets/client_secret.json   (gitignored)
  Refresh token      ->  env var, e.g. YT_2AM_REFRESH_TOKEN

Run `python -m faceless_fleet.pipeline.upload <channel> --auth` once locally to
mint a refresh token interactively.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path

from .config import ROOT, load_channel, output_dirs
from .schedule import next_publish_at

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SECRETS = ROOT / "secrets"
RETRIABLE = {500, 502, 503, 504}


def _client_secret_path() -> Path:
    return SECRETS / "client_secret.json"


def interactive_auth(slug: str, manual: bool = False,
                     redirect_host: str | None = None, port: int = 8080) -> None:
    """One-time: consent and print the refresh token to store as a secret.

    Three modes — pick the one that fits how you'll click "approve":

      (default) desktop browser on the SAME machine running this:
          python -m faceless_fleet.pipeline.upload <ch> --auth

      --redirect-host <VPS_PUBLIC_IP>  (PHONE-FRIENDLY, recommended):
          Run this on the VPS. It serves on 0.0.0.0:<port> and prints ONE link.
          Open that link on your phone, tap Approve, and Google redirects back to
          the VPS which captures the token automatically — no copy-paste.
          Register  http://<VPS_PUBLIC_IP>:<port>/  as an Authorized redirect URI
          on a "Web application" OAuth client, and open the port in the firewall.

      --manual  (works anywhere, incl. phone, with one paste):
          Prints a link. Open on phone, Approve, then copy the FULL redirected
          URL (it'll fail to load — that's fine) and paste it back here.
    """
    cfg = load_channel(slug)
    env_name = cfg["channel"]["oauth_secret_env"]

    if manual:
        from urllib.parse import parse_qs, urlparse

        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_secrets_file(str(_client_secret_path()), SCOPES)
        flow.redirect_uri = "http://localhost"
        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
        print("\n1) On your phone, open this link and tap Approve:\n\n", auth_url, "\n")
        print("2) It will redirect to a 'localhost' page that won't load — that's expected.")
        print("3) Copy the FULL URL from the address bar and paste it below.\n")
        resp = input("Paste the redirected URL (or just the code): ").strip()
        code = parse_qs(urlparse(resp).query).get("code", [resp])[0]
        flow.fetch_token(code=code)
        creds = flow.credentials
    else:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(_client_secret_path()), SCOPES)
        if redirect_host:
            creds = flow.run_local_server(
                host="0.0.0.0", port=port, open_browser=False,
                redirect_uri_trailing_slash=True,
                authorization_prompt_message=(
                    f"\n>>> Open this on your phone and tap Approve:\n{{url}}\n"
                    f"(redirects to http://{redirect_host}:{port}/ — register that URI)\n"),
                bind_addr="0.0.0.0")
        else:
            creds = flow.run_local_server(port=0)

    print("\n=== STORE THIS as the secret/env var below (keep it private) ===")
    print(f"{env_name}={creds.refresh_token}")


def _service(slug: str):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    cfg = load_channel(slug)
    env_name = cfg["channel"]["oauth_secret_env"]
    refresh = os.environ.get(env_name)
    if not refresh:
        raise RuntimeError(f"Missing refresh token env var {env_name}. Run --auth first.")
    secret = json.loads(_client_secret_path().read_text())["installed"]
    creds = Credentials(
        token=None, refresh_token=refresh,
        token_uri=secret["token_uri"], client_id=secret["client_id"],
        client_secret=secret["client_secret"], scopes=SCOPES)
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds), cfg


def _resumable_insert(youtube, body, media):
    from googleapiclient.errors import HttpError
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response, retry = None, 0
    while response is None:
        try:
            _, response = req.next_chunk()
        except HttpError as e:
            if e.resp.status in RETRIABLE and retry < 6:
                sleep = (2 ** retry) + random.random()
                print(f"[upload] {e.resp.status} retry in {sleep:.1f}s")
                time.sleep(sleep); retry += 1
                continue
            raise
    return response["id"]


def upload_one(slug: str, video: Path, dry_run: bool = False) -> str | None:
    cfg = load_channel(slug)
    plan_path = video.with_suffix(".plan.json")
    plan = json.loads(plan_path.read_text()) if plan_path.exists() else {}
    md = plan.get("metadata", cfg["metadata"])
    title = plan.get("title") or md.get("title_templates", ["untitled"])[0]
    publish_at = next_publish_at(cfg, seed=video.name)

    body = {
        "snippet": {
            "title": title[:100],
            "description": md.get("description", ""),
            "tags": md.get("tags", []),
            "categoryId": str(cfg["upload"].get("category_id", "10")),
        },
        "status": {
            "privacyStatus": cfg["upload"].get("privacy_status", "private"),
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": bool(md.get("made_for_kids", False)),
        },
    }
    print(f"[upload] {slug}: {video.name}\n  title: {title}\n  publishAt: {publish_at}")
    if dry_run:
        print("  (dry-run — not uploaded)")
        return None

    from googleapiclient.http import MediaFileUpload
    youtube, _ = _service(slug)
    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True)
    vid = _resumable_insert(youtube, body, media)
    print(f"  uploaded: https://youtu.be/{vid}  (publishes {publish_at})")

    # move to published/ with a record
    dirs = output_dirs(cfg)
    dest = dirs["published"] / video.name
    video.rename(dest)
    dest.with_suffix(".published.json").write_text(json.dumps(
        {"video_id": vid, "title": title, "publish_at": publish_at}, indent=2))
    return vid


def upload_queue(slug: str, dry_run: bool = False, limit: int = 1) -> None:
    cfg = load_channel(slug)
    dirs = output_dirs(cfg)
    approved = sorted(dirs["approved"].glob("*.mp4"))[:limit]
    if not approved:
        print(f"[upload] approved queue empty for {slug}")
        return
    for v in approved:
        upload_one(slug, v, dry_run=dry_run)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("--auth", action="store_true", help="one-time interactive OAuth")
    ap.add_argument("--manual", action="store_true", help="phone: approve + paste the redirected URL")
    ap.add_argument("--redirect-host", help="phone: VPS public IP to redirect back to")
    ap.add_argument("--port", type=int, default=8080, help="port for --redirect-host mode")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=1, help="max videos to drip this run")
    args = ap.parse_args()
    if args.auth:
        interactive_auth(args.channel, manual=args.manual,
                         redirect_host=args.redirect_host, port=args.port)
    else:
        upload_queue(args.channel, dry_run=args.dry_run, limit=args.limit)
