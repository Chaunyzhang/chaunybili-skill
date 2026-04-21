#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bili_core import capability_gate, run


def main() -> None:
    gate = capability_gate("download")
    if not gate.get("ready"):
        print(json.dumps({"success": False, "message": gate.get("message"), "prepare_summary": gate.get("prepare_summary")}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    parser = argparse.ArgumentParser(description="Bilibili download workflow")
    parser.add_argument("url")
    parser.add_argument("--output-dir", default=str(Path.cwd() / "out"))
    parser.add_argument("--quality", default="1080p")
    parser.add_argument("--format", default="mp3")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--batch", action="store_true")
    args = parser.parse_args()

    if args.batch:
        urls = [part.strip() for part in args.url.split(",") if part.strip()]
        result = run("downloader", "batch_download", urls=urls, quality=args.quality, output_dir=args.output_dir, format=args.format)
    else:
        result = run("downloader", "download", url=args.url, quality=args.quality, output_dir=args.output_dir, format=args.format, page=args.page)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
