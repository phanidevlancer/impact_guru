"""
Campaign runner — sends batches of Telegram messages and tracks progress in DB.

Usage:
  # Run a single batch of 10 messages
  python3 scripts/run_campaign.py --name my_campaign --start +919000000000 --link "https://impactguru.com/..."

  # Run continuously (batch every hour)
  python3 scripts/run_campaign.py --name my_campaign --start +919000000000 --link "https://..." --schedule --batch-delay 3600

  # Custom batch size and message intervals
  python3 scripts/run_campaign.py --name my_campaign --start +919000000000 --link "https://..." \
      --batch-size 10 --min-delay 45 --max-delay 90 --schedule
"""

import asyncio
import argparse
import logging

from app.campaign import run_batch, run_scheduled

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="ImpactGuru Telegram Campaign Runner")

    parser.add_argument("--name",        required=True, help="Campaign name (used as DB key)")
    parser.add_argument("--start",       required=True, help="Starting phone number e.g. +919000000000")
    parser.add_argument("--link",        required=True, help="ImpactGuru fundraising link")
    parser.add_argument("--batch-size",  type=int, default=10,   help="Messages per batch (default: 10)")
    parser.add_argument("--min-delay",   type=int, default=30,   help="Min seconds between messages (default: 30)")
    parser.add_argument("--max-delay",   type=int, default=120,  help="Max seconds between messages (default: 120)")
    parser.add_argument("--schedule",    action="store_true",    help="Run continuously (multiple batches)")
    parser.add_argument("--batch-delay", type=int, default=3600, help="Seconds between batches when --schedule (default: 3600)")
    parser.add_argument("--max-batches", type=int, default=None, help="Stop after N batches (default: unlimited)")

    return parser.parse_args()


async def main():
    args = parse_args()

    if args.schedule:
        await run_scheduled(
            campaign_name=args.name,
            start_number=args.start,
            link=args.link,
            batch_size=args.batch_size,
            batch_delay=args.batch_delay,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            max_batches=args.max_batches,
        )
    else:
        await run_batch(
            campaign_name=args.name,
            start_number=args.start,
            link=args.link,
            batch_size=args.batch_size,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
