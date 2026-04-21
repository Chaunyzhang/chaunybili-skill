#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bili_impl.auth import BilibiliAuth
from bili_impl.utils import API_SEARCH, DEFAULT_HEADERS, extract_bvid, format_duration, format_number
from bili_core import capability_gate


def build_client() -> httpx.Client:
    auth = BilibiliAuth()
    if auth.is_authenticated:
        return httpx.Client(headers=auth.get_headers(), cookies=auth.cookies, timeout=30.0, follow_redirects=True)
    return httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0, follow_redirects=True)


def parse_video_item(item: dict[str, Any]) -> dict[str, Any]:
    duration_value = item.get("duration", 0)
    if isinstance(duration_value, str):
        duration_text = duration_value
    else:
        duration_text = format_duration(int(duration_value or 0))
    return {
        "bvid": item.get("bvid"),
        "aid": item.get("aid"),
        "title": item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
        "description": item.get("description", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
        "duration": duration_text,
        "author": item.get("author"),
        "mid": item.get("mid"),
        "play": item.get("play", 0),
        "play_formatted": format_number(int(item.get("play", 0) or 0)),
        "favorites": item.get("favorites", 0),
        "favorites_formatted": format_number(int(item.get("favorites", 0) or 0)),
        "comment": item.get("comment", 0),
        "comment_formatted": format_number(int(item.get("comment", 0) or 0)),
        "typename": item.get("typename", ""),
        "pubdate": item.get("pubdate"),
        "pic": ("https:" + item.get("pic")) if str(item.get("pic", "")).startswith("//") else item.get("pic", ""),
        "url": f"https://www.bilibili.com/video/{item.get('bvid')}" if item.get("bvid") else "",
    }


def search_videos(keyword: str, page: int = 1, page_size: int = 10, order: str = "totalrank", duration: int = 0) -> dict[str, Any]:
    params = {
        "search_type": "video",
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
        "order": order,
        "duration": duration,
    }
    with build_client() as client:
        resp = client.get(API_SEARCH, params=params)
        try:
            data = resp.json()
        except Exception:
            data = None

    if not data:
        return search_videos_web(keyword, page=page, page_size=page_size)

    if data.get("code") != 0:
        return {"success": False, "message": data.get("message", "API error")}

    result = data.get("data", {}) or {}
    items = [parse_video_item(item) for item in result.get("result", [])]
    return {
        "success": True,
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
        "num_results": result.get("numResults", 0),
        "num_pages": result.get("numPages", 0),
        "videos": items,
    }


def search_videos_web(keyword: str, page: int = 1, page_size: int = 10) -> dict[str, Any]:
    search_url = f"https://search.bilibili.com/all?keyword={quote(keyword)}&page={page}"
    with build_client() as client:
        resp = client.get(search_url)
    html = resp.text
    soup = BeautifulSoup(html, "lxml")
    items = []
    for card in soup.select("div.bili-video-card, div.video-item"):
        a = card.select_one("a[href*='/video/']")
        if not a:
            continue
        href = a.get("href", "")
        title = (a.get("title") or a.get_text(" ", strip=True) or "").strip()
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://www.bilibili.com" + href
        items.append(
            {
                "bvid": extract_bvid(href),
                "aid": None,
                "title": title,
                "description": "",
                "duration": "",
                "author": "",
                "mid": None,
                "play": 0,
                "play_formatted": "0",
                "favorites": 0,
                "favorites_formatted": "0",
                "comment": 0,
                "comment_formatted": "0",
                "typename": "",
                "pubdate": None,
                "pic": "",
                "url": href,
                "source": "web_fallback",
            }
        )
        if len(items) >= page_size:
            break
    return {
        "success": bool(items),
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
        "num_results": len(items),
        "num_pages": None,
        "videos": items,
        "source": "web_fallback",
        "message": "" if items else "Web fallback produced no results",
    }


def main() -> None:
    gate = capability_gate("search")
    if not gate.get("ready"):
        print(json.dumps({"success": False, "message": gate.get("message"), "prepare_summary": gate.get("prepare_summary")}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    parser = argparse.ArgumentParser(description="Bilibili search workflow")
    parser.add_argument("keyword")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--order", default="totalrank", choices=["totalrank", "click", "pubdate", "dm", "stow"])
    parser.add_argument("--duration", type=int, default=0, choices=[0, 1, 2, 3, 4])
    args = parser.parse_args()

    result = search_videos(args.keyword, page=args.page, page_size=args.page_size, order=args.order, duration=args.duration)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
