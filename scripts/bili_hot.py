#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from bili_core import capability_gate, run


def main() -> None:
    gate = capability_gate("hot")
    if not gate.get("ready"):
        print(json.dumps({"success": False, "message": gate.get("message"), "prepare_summary": gate.get("prepare_summary")}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    parser = argparse.ArgumentParser(description="Bilibili hot monitor workflow")
    parser.add_argument("--mode", choices=["hot", "trending", "weekly", "rank"], default="hot")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--category", default="all")
    args = parser.parse_args()

    if args.mode == "hot":
        result = run("hot_monitor", "get_hot", page=args.page, page_size=args.page_size)
    elif args.mode == "trending":
        result = run("hot_monitor", "get_trending", limit=args.limit)
    elif args.mode == "weekly":
        result = run("hot_monitor", "get_weekly")
    else:
        result = run("hot_monitor", "get_rank", category=args.category, limit=args.limit)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
