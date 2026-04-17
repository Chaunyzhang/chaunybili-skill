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
IMPL_ROOT = ROOT / "bili_impl"
DATA_DIR = Path.home() / ".local" / "share" / "chaunybili-skill"
CREDENTIALS_PATH = DATA_DIR / "credentials.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bili_impl import BilibiliAuth, BilibiliDownloader, BilibiliPlayer, BilibiliWatcher, HotMonitor, SubtitleDownloader  # noqa: E402


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


class BilibiliReadCore:
    def __init__(self) -> None:
        creds = read_credentials()
        self.auth = BilibiliAuth(
            sessdata=creds.get("sessdata") or None,
            bili_jct=creds.get("bili_jct") or None,
            buvid3=creds.get("buvid3") or None,
            credential_file=str(CREDENTIALS_PATH) if CREDENTIALS_PATH.is_file() else None,
            persist=False,
        )
        self.hot_monitor = HotMonitor(auth=self.auth)
        self.downloader = BilibiliDownloader(auth=self.auth)
        self.watcher = BilibiliWatcher(auth=self.auth)
        self.player = BilibiliPlayer(auth=self.auth)
        self.subtitle = SubtitleDownloader(auth=self.auth, downloader=self.downloader, player=self.player)

    async def execute(self, module: str, action: str, **kwargs) -> dict[str, Any]:
        mapping = {
            "hot_monitor": self.hot_monitor,
            "downloader": self.downloader,
            "watcher": self.watcher,
            "subtitle": self.subtitle,
            "player": self.player,
        }
        target = mapping.get(module)
        if not target:
            return {
                "success": False,
                "message": f"Unknown module: {module}. Allowed modules: {list(mapping.keys())}",
            }
        return await target.execute(action=action, **kwargs)


def build_app() -> BilibiliReadCore:
    return BilibiliReadCore()


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
        "impl_root": str(IMPL_ROOT),
        "impl_package_exists": (IMPL_ROOT / "__init__.py").is_file(),
        "credentials_path": str(CREDENTIALS_PATH),
        "credentials_file_exists": CREDENTIALS_PATH.is_file(),
        "sessdata_present": bool(creds.get("sessdata")),
        "read_only_ready": (IMPL_ROOT / "__init__.py").is_file(),
        "publish_ready": bool(creds.get("sessdata")) and bool(creds.get("bili_jct")),
        "write_actions_default": "disabled",
    }
