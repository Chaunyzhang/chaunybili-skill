#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from bili_core import capability_gate, run


def main() -> None:
    gate = capability_gate("watch")
    if not gate.get("ready"):
        print(json.dumps({"success": False, "message": gate.get("message"), "prepare_summary": gate.get("prepare_summary")}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    parser = argparse.ArgumentParser(description="Bilibili stats workflow")
    parser.add_argument("--mode", choices=["watch", "stats", "compare"], default="stats")
    parser.add_argument("url")
    args = parser.parse_args()

    if args.mode == "watch":
        result = run("watcher", "watch", url=args.url)
    elif args.mode == "compare":
        urls = [part.strip() for part in args.url.split(",") if part.strip()]
        result = run("watcher", "compare", urls=urls)
    else:
        result = run("watcher", "get_stats", url=args.url)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
