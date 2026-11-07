"""Command line entry points.

  python -m app.cli healthcheck
  python -m app.cli ingest-medlineplus --date 2026-11-03
  python -m app.cli ingest-medlineplus --xml-file tests/fixtures/mplus_sample.xml --corpus-version 2026-01-01
  python -m app.cli search "high blood pressure"
"""
import argparse
import asyncio
import itertools
import json
import re
import sys
import tempfile
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app.config import get_settings
from app.db import check_database
from app.inference_client import InferenceClient

_FILE_DATE = re.compile(r"mplus_topics_(\d{4}-\d{2}-\d{2})\.xml")


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


def cmd_ingest_medlineplus(args) -> int:
    from sqlalchemy.exc import SQLAlchemyError

    from app.db import get_engine
    from app.ingestion.medlineplus import ParseReport, build_xml_url, download_xml, parse_topics
    from app.ingestion.store import ingest_topics

    corpus_version = args.corpus_version
    if args.xml_file and not corpus_version:
        match = _FILE_DATE.search(Path(args.xml_file).name)
        corpus_version = match.group(1) if match else None
    if args.date:
        corpus_version = corpus_version or args.date
    try:
        if not corpus_version:
            raise ValueError("cannot infer the corpus version; pass --corpus-version YYYY-MM-DD")
        date.fromisoformat(corpus_version)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    parse_report = ParseReport()
    try:
        with tempfile.TemporaryDirectory() as scratch:
            if args.date:
                path = Path(scratch) / "topics.xml"
                size = download_xml(build_xml_url(args.date), path)
                print(f"Downloaded {size} bytes from medlineplus.gov", file=sys.stderr)
            else:
                path = Path(args.xml_file)
            topics = parse_topics(path, args.language, parse_report)
            if args.max_topics:
                topics = itertools.islice(topics, args.max_topics)
            report = ingest_topics(
                get_engine(), topics, corpus_version, full_run=not args.max_topics
            )
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except SQLAlchemyError as error:
        print(
            f"ERROR: database problem ({type(error).__name__}). "
            "Have the migrations been applied (scripts/migrate)?",
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "ingest": asdict(report),
                "parse": {"parsed": parse_report.parsed, "skipped": dict(parse_report.skipped)},
            },
            indent=2,
        )
    )
    return 0


def cmd_search(args) -> int:
    from sqlalchemy.exc import SQLAlchemyError

    from app.search import search_chunks

    try:
        rows = search_chunks(args.query, args.limit)
    except SQLAlchemyError as error:
        print(f"ERROR: database problem ({type(error).__name__}).", file=sys.stderr)
        return 1
    if not rows:
        print("No passages found.")
        return 0
    for number, row in enumerate(rows, start=1):
        passage_id = f"{row['source_id']}:{row['external_id']}:{row['chunk_index']}"
        snippet = " ".join(row["text"].split())[:160]
        print(f"{number}. [{row['score']:.3f}] {row['title']} ({passage_id})")
        print(f"   {row['url']}")
        print(f"   {snippet}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("healthcheck", help="Check database and inference reachability.")

    ingest = sub.add_parser("ingest-medlineplus", help="Ingest MedlinePlus health topic summaries.")
    source = ingest.add_mutually_exclusive_group(required=True)
    source.add_argument("--xml-file", help="Path to a health topic XML file.")
    source.add_argument("--date", help="Download the file published on YYYY-MM-DD (Tuesday to Saturday).")
    ingest.add_argument("--corpus-version", help="YYYY-MM-DD; inferred from the file name or --date.")
    ingest.add_argument("--language", default="English", choices=["English", "Spanish"])
    ingest.add_argument("--max-topics", type=int, help="Ingest only the first N topics (testing).")

    search = sub.add_parser("search", help="Keyword search over ingested passages.")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)

    args = parser.parse_args(argv)
    if args.command == "healthcheck":
        return cmd_healthcheck()
    if args.command == "ingest-medlineplus":
        return cmd_ingest_medlineplus(args)
    if args.command == "search":
        return cmd_search(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
