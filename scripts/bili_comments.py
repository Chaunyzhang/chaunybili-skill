#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from bili_impl.auth import BilibiliAuth
from bili_impl.utils import API_COMMENTS, API_VIDEO_INFO, DEFAULT_HEADERS, extract_bvid


def build_client() -> httpx.Client:
    auth = BilibiliAuth()
    if auth.is_authenticated:
        return httpx.Client(headers=auth.get_headers(), cookies=auth.cookies, timeout=30.0, follow_redirects=True)
    return httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0, follow_redirects=True)


def resolve_aid_and_title(url_or_bvid: str) -> tuple[int | None, str]:
    bvid = extract_bvid(url_or_bvid)
    if not bvid:
        return None, ""
    with build_client() as client:
        resp = client.get(API_VIDEO_INFO, params={"bvid": bvid})
        data = resp.json()
    if data.get("code") != 0:
        return None, ""
    video = data.get("data", {}) or {}
    return video.get("aid"), video.get("title", "")


def parse_reply(reply: dict[str, Any]) -> dict[str, Any]:
    member = reply.get("member", {}) or {}
    content = reply.get("content", {}) or {}
    replies = []
    for child in reply.get("replies", []) or []:
        child_member = child.get("member", {}) or {}
        child_content = child.get("content", {}) or {}
        replies.append(
            {
                "rpid": child.get("rpid"),
                "user": child_member.get("uname", ""),
                "mid": child_member.get("mid"),
                "message": child_content.get("message", ""),
                "like": child.get("like", 0),
                "ctime": child.get("ctime", 0),
            }
        )
    return {
        "rpid": reply.get("rpid"),
        "user": member.get("uname", ""),
        "mid": member.get("mid"),
        "message": content.get("message", ""),
        "like": reply.get("like", 0),
        "ctime": reply.get("ctime", 0),
        "reply_count": reply.get("rcount", 0),
        "replies": replies,
    }


def fetch_comments(url_or_bvid: str, page: int = 1, page_size: int = 10, sort: int = 2) -> dict[str, Any]:
    aid, title = resolve_aid_and_title(url_or_bvid)
    if not aid:
        return {"success": False, "message": f"Could not resolve aid from {url_or_bvid}"}

    params = {
        "type": 1,
        "oid": aid,
        "pn": page,
        "ps": page_size,
        "sort": sort,
    }
    with build_client() as client:
        resp = client.get(API_COMMENTS, params=params)
        data = resp.json()

    if data.get("code") != 0:
        return {"success": False, "message": data.get("message", "API error")}

    replies = (data.get("data", {}) or {}).get("replies", []) or []
    parsed = [parse_reply(reply) for reply in replies]
    page_info = (data.get("data", {}) or {}).get("page", {}) or {}
    return {
        "success": True,
        "aid": aid,
        "title": title,
        "page": page_info.get("num", page),
        "page_size": page_info.get("size", page_size),
        "count": page_info.get("count", len(parsed)),
        "comments": parsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bilibili comments workflow")
    parser.add_argument("target", help="Bilibili URL or BV id")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--sort", type=int, default=2, choices=[0, 2], help="0=by time, 2=by hot")
    args = parser.parse_args()

    result = fetch_comments(args.target, page=args.page, page_size=args.page_size, sort=args.sort)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
