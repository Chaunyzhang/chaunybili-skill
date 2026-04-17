#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from bili_impl.auth import BilibiliAuth
from bili_impl.utils import API_NAV, API_SPACE_INFO, API_SPACE_VIDEOS, DEFAULT_HEADERS, extract_wbi_keys, generate_wbi_sign


def build_client() -> httpx.Client:
    auth = BilibiliAuth()
    if auth.is_authenticated:
        return httpx.Client(headers=auth.get_headers(), cookies=auth.cookies, timeout=30.0, follow_redirects=True)
    return httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0, follow_redirects=True)


def signed_params(client: httpx.Client, params: dict[str, Any]) -> dict[str, Any]:
    nav = client.get(API_NAV).json()
    img_key, sub_key = extract_wbi_keys(nav)
    if not img_key or not sub_key:
        return params
    return generate_wbi_sign(params, img_key, sub_key)


def get_creator_profile(mid: int) -> dict[str, Any]:
    with build_client() as client:
        resp = client.get(API_SPACE_INFO, params=signed_params(client, {"mid": mid}))
        try:
            data = resp.json()
        except Exception:
            data = None

    if not data or data.get("code") != 0:
        fallback = get_creator_profile_web(mid)
        if fallback.get("success"):
            return fallback
        return {"success": False, "message": data.get("message", "API error") if isinstance(data, dict) else "non-json response"}

    profile = data.get("data", {}) or {}
    return {
        "success": True,
        "mid": mid,
        "name": profile.get("name", ""),
        "sex": profile.get("sex", ""),
        "face": profile.get("face", ""),
        "sign": profile.get("sign", ""),
        "level": (profile.get("level_info", {}) or {}).get("current_level"),
        "fans": profile.get("fans", 0),
        "friend": profile.get("friend", 0),
        "archive_count": profile.get("archive_count", 0),
        "article_count": profile.get("article_count", 0),
        "follower": profile.get("follower", 0),
        "official": profile.get("official", {}) or {},
        "live_room": profile.get("live_room", {}) or {},
    }


def get_creator_videos(mid: int, page: int = 1, page_size: int = 10, order: str = "pubdate") -> dict[str, Any]:
    params = {
        "mid": mid,
        "pn": page,
        "ps": page_size,
        "order": order,
    }
    with build_client() as client:
        resp = client.get(API_SPACE_VIDEOS, params=signed_params(client, params))
        try:
            data = resp.json()
        except Exception:
            data = None

    if not data or data.get("code") != 0:
        fallback = get_creator_videos_web(mid, page=page, page_size=page_size)
        if fallback.get("success"):
            return fallback
        return {"success": False, "message": data.get("message", "API error") if isinstance(data, dict) else "non-json response"}

    block = (data.get("data", {}) or {}).get("list", {}) or {}
    vlist = block.get("vlist", []) or []
    videos = []
    for item in vlist:
        videos.append(
            {
                "bvid": item.get("bvid"),
                "aid": item.get("aid"),
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "created": item.get("created", 0),
                "length": item.get("length", ""),
                "play": item.get("play", 0),
                "comment": item.get("comment", 0),
                "pic": ("https:" + item.get("pic")) if str(item.get("pic", "")).startswith("//") else item.get("pic", ""),
                "url": f"https://www.bilibili.com/video/{item.get('bvid')}" if item.get("bvid") else "",
            }
        )
    page_info = (data.get("data", {}) or {}).get("page", {}) or {}
    return {
        "success": True,
        "mid": mid,
        "page": page_info.get("pn", page),
        "page_size": page_info.get("ps", page_size),
        "count": page_info.get("count", len(videos)),
        "videos": videos,
    }


def get_creator_profile_web(mid: int) -> dict[str, Any]:
    url = f"https://space.bilibili.com/{mid}"
    with build_client() as client:
        resp = client.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    cleaned = title
    for suffix in [
        "的个人空间-哔哩哔哩视频",
        "个人空间-哔哩哔哩视频",
        "的个人空间-",
    ]:
        cleaned = cleaned.replace(suffix, "")
    cleaned = cleaned.strip(" -")
    return {
        "success": bool(title),
        "mid": mid,
        "name": cleaned or title,
        "sex": "",
        "face": "",
        "sign": "",
        "level": None,
        "fans": 0,
        "friend": 0,
        "archive_count": 0,
        "article_count": 0,
        "follower": 0,
        "official": {},
        "live_room": {},
        "source": "web_fallback",
    }


def get_creator_videos_web(mid: int, page: int = 1, page_size: int = 10) -> dict[str, Any]:
    url = f"https://space.bilibili.com/{mid}/video?tid=0&pn={page}"
    with build_client() as client:
        resp = client.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
    videos = []
    seen = set()
    for a in soup.select("a[href*='/video/']"):
        href = a.get("href", "")
        title = (a.get("title") or a.get_text(" ", strip=True) or "").strip()
        if not title:
            continue
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://www.bilibili.com" + href
        if "/video/" not in href or href in seen:
            continue
        seen.add(href)
        videos.append(
            {
                "bvid": None,
                "aid": None,
                "title": title,
                "description": "",
                "created": 0,
                "length": "",
                "play": 0,
                "comment": 0,
                "pic": "",
                "url": href,
                "source": "web_fallback",
            }
        )
        if len(videos) >= page_size:
            break
    return {
        "success": bool(videos),
        "mid": mid,
        "page": page,
        "page_size": page_size,
        "count": len(videos),
        "videos": videos,
        "source": "web_fallback",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bilibili creator workflow")
    parser.add_argument("mid", type=int, help="Creator mid")
    parser.add_argument("--mode", choices=["profile", "videos"], default="profile")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--order", default="pubdate", choices=["pubdate", "click", "stow"])
    args = parser.parse_args()

    if args.mode == "profile":
        result = get_creator_profile(args.mid)
    else:
        result = {
            "success": False,
            "message": "creator video listing is temporarily disabled in the aggregated skill because the current path is too prone to risk controls or unstable non-JSON responses.",
            "safety_default": "disabled_until_stable",
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
