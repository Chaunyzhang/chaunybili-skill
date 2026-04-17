#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bili_core import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Bilibili subtitle workflow")
    parser.add_argument("--mode", choices=["list", "download", "convert", "merge"], default="list")
    parser.add_argument("target")
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--format", default="srt")
    parser.add_argument("--output-dir", default=str(Path.cwd() / "out"))
    parser.add_argument("--output-path", default="")
    args = parser.parse_args()

    if args.mode == "list":
        result = run("subtitle", "list", url=args.target)
    elif args.mode == "download":
        result = run("subtitle", "download", url=args.target, language=args.language, format=args.format, output_dir=args.output_dir)
    elif args.mode == "convert":
        result = run("subtitle", "convert", input_path=args.target, output_format=args.format, output_dir=args.output_dir)
    else:
        input_paths = [part.strip() for part in args.target.split(",") if part.strip()]
        result = run("subtitle", "merge", input_paths=input_paths, output_path=args.output_path, output_format=args.format)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
