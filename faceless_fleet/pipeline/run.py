"""Orchestrator CLI — thin wrapper over the stages.

  python -m faceless_fleet.pipeline.run generate <channel>
  python -m faceless_fleet.pipeline.run assemble <channel> [--variant 3h]
  python -m faceless_fleet.pipeline.run review  <channel>            # list pending + policy flags
  python -m faceless_fleet.pipeline.run approve <channel> --file X   # human gate
  python -m faceless_fleet.pipeline.run upload   <channel> [--dry-run]
  python -m faceless_fleet.pipeline.run channels                     # list configured channels
  python -m faceless_fleet.pipeline.run auto      <channel> [--publish]   # zero-touch single run
  python -m faceless_fleet.pipeline.run weekly    [--channels ...]        # set-and-forget weekly publish
  python -m faceless_fleet.pipeline.run batch-plan <channel> [--budget N] # restock manifest (clips to gen)
  python -m faceless_fleet.pipeline.run fetch-sfx [--only X] [--count N]  # auto-download CC0 audio

The unattended loop on cron is just: generate (-> manifest) ; [Claude/MCP fills it] ;
assemble ; then a SEPARATE jittered cron runs `upload` to drip the approved queue.
`weekly` wraps the whole publish loop for every connected channel — that's the one
cron line you actually need running. `batch-plan` is the periodic clip-restock.
"""
from __future__ import annotations

import argparse

from . import assemble as assemble_mod
from . import generate as generate_mod
from . import review as review_mod
from . import upload as upload_mod
from .config import list_channels


def main() -> None:
    ap = argparse.ArgumentParser(prog="faceless_fleet")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("generate", "assemble", "review", "approve", "upload"):
        p = sub.add_parser(name)
        p.add_argument("channel")
        if name == "assemble":
            p.add_argument("--variant", default="3h")
        if name == "approve":
            p.add_argument("--file", required=True)
        if name == "upload":
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--limit", type=int, default=1)
    sub.add_parser("channels")

    pa = sub.add_parser("auto")          # the zero-touch loop
    pa.add_argument("channel")
    pa.add_argument("--variant", default="8h")
    pa.add_argument("--no-approve", dest="approve", action="store_false")
    pa.add_argument("--publish", action="store_true")

    pf = sub.add_parser("fetch-sfx")     # auto-download CC0 audio
    pf.add_argument("--only")
    pf.add_argument("--count", type=int, default=1)

    pw = sub.add_parser("weekly")        # the set-and-forget weekly job
    pw.add_argument("--channels", nargs="*")
    pw.add_argument("--dry-run", action="store_true")

    pb = sub.add_parser("batch-plan")    # budgeted restock manifest (clips to generate)
    pb.add_argument("channel")
    pb.add_argument("--budget", type=float, default=160)

    prr = sub.add_parser("restock-record")  # scheduled session logs a generated clip's URL
    prr.add_argument("channel")
    prr.add_argument("clip_name")
    prr.add_argument("--video-url", required=True)
    prr.add_argument("--image-url")

    prf = sub.add_parser("restock-fetch")    # VPS downloads recorded URLs into the library
    prf.add_argument("channel")

    prn = sub.add_parser("restock-run")      # unattended: generate via Cloud API (needs key)
    prn.add_argument("channel")
    prn.add_argument("--budget", type=float, default=56)

    args = ap.parse_args()
    if args.cmd == "channels":
        print("\n".join(list_channels()))
    elif args.cmd == "generate":
        generate_mod.main(args.channel)
    elif args.cmd == "assemble":
        assemble_mod.assemble(args.channel, args.variant)
    elif args.cmd == "review":
        review_mod.review_queue(args.channel)
    elif args.cmd == "approve":
        review_mod.approve(args.channel, args.file)
    elif args.cmd == "upload":
        upload_mod.upload_queue(args.channel, dry_run=args.dry_run, limit=args.limit)
    elif args.cmd == "auto":
        from . import auto as auto_mod
        auto_mod.auto(args.channel, args.variant, approve=args.approve, publish=args.publish)
    elif args.cmd == "fetch-sfx":
        from . import sfx_fetch
        sfx_fetch.fetch(args.only, args.count)
    elif args.cmd == "weekly":
        from . import weekly
        weekly.run_week(args.channels, publish=not args.dry_run)
    elif args.cmd == "batch-plan":
        from . import batch_plan
        batch_plan.plan(args.channel, args.budget)
    elif args.cmd == "restock-record":
        from . import restock
        restock.record(args.channel, args.clip_name, args.video_url, args.image_url)
    elif args.cmd == "restock-fetch":
        from . import restock
        restock.fetch_pending(args.channel)
    elif args.cmd == "restock-run":
        from . import rest
        rest.fulfill(args.channel, args.budget)


if __name__ == "__main__":
    main()
