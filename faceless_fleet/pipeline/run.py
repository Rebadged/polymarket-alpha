"""Orchestrator CLI — thin wrapper over the stages.

  python -m faceless_fleet.pipeline.run generate <channel>
  python -m faceless_fleet.pipeline.run assemble <channel> [--variant 3h]
  python -m faceless_fleet.pipeline.run review  <channel>            # list pending + policy flags
  python -m faceless_fleet.pipeline.run approve <channel> --file X   # human gate
  python -m faceless_fleet.pipeline.run upload   <channel> [--dry-run]
  python -m faceless_fleet.pipeline.run channels                     # list configured channels

The unattended loop on cron is just: generate (-> manifest) ; [Claude/MCP fills it] ;
assemble ; then a SEPARATE jittered cron runs `upload` to drip the approved queue.
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


if __name__ == "__main__":
    main()
