"""Command line entry points.  Usage: python -m app.cli healthcheck"""
import argparse
import asyncio
import json
import sys

from app.config import get_settings
from app.db import check_database
from app.inference_client import InferenceClient


def cmd_healthcheck() -> int:
    settings = get_settings()
    database = check_database()

    async def probe_inference() -> bool:
        client = InferenceClient(
            base_url=settings.inference_url,
            connect_timeout=settings.inference_connect_timeout,
            read_timeout=settings.inference_read_timeout,
            max_retries=0,
            max_concurrency=1,
        )
        try:
            return await client.health()
        finally:
            await client.aclose()

    inference_ok = asyncio.run(probe_inference())
    report = {**database, "inference": "ok" if inference_ok else "unavailable"}
    print(json.dumps(report, indent=2))
    return 0 if database.get("database") == "ok" and inference_ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("healthcheck", help="Check database and inference reachability.")
    args = parser.parse_args(argv)
    if args.command == "healthcheck":
        return cmd_healthcheck()
    return 2


if __name__ == "__main__":
    sys.exit(main())
