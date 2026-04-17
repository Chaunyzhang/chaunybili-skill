from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
VENDOR_ROOT = ROOT / "vendor" / "bilibili_all_in_one"
DATA_DIR = Path.home() / ".local" / "share" / "chaunybili-skill"
CREDENTIALS_PATH = DATA_DIR / "credentials.json"

if str(VENDOR_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_ROOT))

from main import BilibiliAllInOne  # type: ignore  # noqa: E402


SAFE_READ_MODULES = {
    "hot_monitor": {"get_hot", "get_trending", "get_weekly", "get_rank"},
    "downloader": {"get_info", "get_formats", "download", "batch_download"},
    "watcher": {"watch", "get_stats", "track", "compare"},
    "subtitle": {"list", "download", "convert", "merge"},
    "player": {"play", "get_playurl", "get_danmaku", "get_playlist"},
}

DISABLED_WRITE_MODULES = {
    "publisher": {
        "upload",
        "draft",
        "schedule",
        "edit",
    }
}


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_credentials() -> dict[str, Any]:
    ensure_directories()
    env = {
        "sessdata": os.getenv("BILIBILI_SESSDATA", ""),
        "bili_jct": os.getenv("BILIBILI_BILI_JCT", ""),
        "buvid3": os.getenv("BILIBILI_BUVID3", ""),
    }
    if env["sessdata"]:
        return env

    if CREDENTIALS_PATH.is_file():
        try:
            data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {
                    "sessdata": data.get("sessdata", ""),
                    "bili_jct": data.get("bili_jct", ""),
                    "buvid3": data.get("buvid3", ""),
                }
        except Exception:
            pass
    return env


def has_auth() -> bool:
    creds = read_credentials()
    return bool(creds.get("sessdata"))


def build_app() -> BilibiliAllInOne:
    creds = read_credentials()
    return BilibiliAllInOne(
        sessdata=creds.get("sessdata") or None,
        bili_jct=creds.get("bili_jct") or None,
        buvid3=creds.get("buvid3") or None,
        credential_file=str(CREDENTIALS_PATH) if CREDENTIALS_PATH.is_file() else None,
        persist=False,
    )


async def execute(module: str, action: str, **kwargs) -> dict[str, Any]:
    if module in DISABLED_WRITE_MODULES and action in DISABLED_WRITE_MODULES[module]:
        return {
            "success": False,
            "message": f"{module}.{action} is intentionally disabled in this aggregated skill because it is a high-risk write action.",
            "safety_default": "read_mostly",
        }

    app = build_app()
    return await app.execute(module, action, **kwargs)


def run(module: str, action: str, **kwargs) -> dict[str, Any]:
    return asyncio.run(execute(module, action, **kwargs))


def health_snapshot() -> dict[str, Any]:
    ensure_directories()
    creds = read_credentials()
    return {
        "data_dir": str(DATA_DIR),
        "vendor_root": str(VENDOR_ROOT),
        "vendor_main_exists": (VENDOR_ROOT / "main.py").is_file(),
        "vendor_src_exists": (VENDOR_ROOT / "src" / "__init__.py").is_file(),
        "credentials_path": str(CREDENTIALS_PATH),
        "credentials_file_exists": CREDENTIALS_PATH.is_file(),
        "sessdata_present": bool(creds.get("sessdata")),
        "read_only_ready": (VENDOR_ROOT / "main.py").is_file() and (VENDOR_ROOT / "src" / "__init__.py").is_file(),
        "publish_ready": bool(creds.get("sessdata")) and bool(creds.get("bili_jct")),
        "write_actions_default": "disabled",
    }
