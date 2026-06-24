from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .collector import collect_html_snapshot, collect_visible_text, fetch_public_url
from .encoding import SUPPORTED_PLATFORMS, build_search_url


def dump_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ozon-source-collector")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-url", help="Build a public frontend search URL")
    build.add_argument("--platform", choices=SUPPORTED_PLATFORMS, required=True)
    build.add_argument("--keyword", required=True)

    parse_html = sub.add_parser("parse-html", help="Parse a saved frontend HTML snapshot")
    parse_html.add_argument("--platform", choices=SUPPORTED_PLATFORMS, required=True)
    parse_html.add_argument("--url")
    parse_html.add_argument("--input", required=True)

    parse_text = sub.add_parser("parse-text", help="Parse copied visible frontend text")
    parse_text.add_argument("--platform", choices=SUPPORTED_PLATFORMS, required=True)
    parse_text.add_argument("--url")
    parse_text.add_argument("--input", required=True)

    fetch = sub.add_parser("fetch-url", help="Fetch one public URL with a strict safety gate")
    fetch.add_argument("--platform", choices=SUPPORTED_PLATFORMS, required=True)
    fetch.add_argument("--url", required=True)
    fetch.add_argument("--allow-network", action="store_true")
    fetch.add_argument("--delay-seconds", type=float, default=8.0)

    args = parser.parse_args(argv)

    if args.command == "build-url":
        dump_json({"platform": args.platform, "keyword": args.keyword, "url": build_search_url(args.platform, args.keyword)})
        return 0
    if args.command == "parse-html":
        dump_json(collect_html_snapshot(args.platform, args.url, read_text(args.input)).to_dict())
        return 0
    if args.command == "parse-text":
        dump_json(collect_visible_text(args.platform, args.url, read_text(args.input)).to_dict())
        return 0
    if args.command == "fetch-url":
        dump_json(
            fetch_public_url(
                args.platform,
                args.url,
                allow_network=args.allow_network,
                delay_seconds=args.delay_seconds,
            ).to_dict()
        )
        return 0

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())