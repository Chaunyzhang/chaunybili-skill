#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from bili_core import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Bilibili player workflow")
    parser.add_argument("--mode", choices=["play", "playurl", "danmaku", "playlist"], default="play")
    parser.add_argument("url")
    parser.add_argument("--quality", default="1080p")
    parser.add_argument("--page", type=int, default=1)
    args = parser.parse_args()

    if args.mode == "play":
        result = run("player", "play", url=args.url, quality=args.quality, page=args.page)
    elif args.mode == "playurl":
        result = run("player", "get_playurl", url=args.url, quality=args.quality, page=args.page)
    elif args.mode == "danmaku":
        result = run("player", "get_danmaku", url=args.url, page=args.page)
    else:
        result = run("player", "get_playlist", url=args.url)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
