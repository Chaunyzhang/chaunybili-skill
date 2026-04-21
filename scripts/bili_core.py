from __future__ import annotations

import asyncio
import json
import os
import sys
import hashlib
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
PREP_STATE = DATA_DIR / "prepare-state.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bili_impl import BilibiliAuth, BilibiliDownloader, BilibiliPlayer, BilibiliWatcher, HotMonitor, SubtitleDownloader  # noqa: E402
from prepare_state import read_prepare_state


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
    payload = {
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
    payload["runtime_signature"] = runtime_signature_from_snapshot(payload)
    payload["prepare_state"] = prepare_state_summary(payload)
    payload["prepared_workflows_ready"] = payload["prepare_state"].get("prepared_workflows_ready", False)
    payload["all_ready"] = bool(payload["read_only_ready"] and payload["prepare_state"].get("state_exists") and payload["prepare_state"].get("signature_matches") and payload["prepared_workflows_ready"])
    return payload


def runtime_signature_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    signature = {
        "impl_package_exists": snapshot.get("impl_package_exists"),
        "credentials_file_exists": snapshot.get("credentials_file_exists"),
        "sessdata_present": snapshot.get("sessdata_present"),
        "publish_ready": snapshot.get("publish_ready"),
    }
    digest = hashlib.sha256(json.dumps(signature, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {**signature, "digest": digest}


def prepare_state_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    state = read_prepare_state(PREP_STATE)
    current_signature = runtime_signature_from_snapshot(snapshot)
    saved_signature = state.get("runtime_signature", {}) if isinstance(state, dict) else {}
    signature_matches = bool(saved_signature) and saved_signature.get("digest") == current_signature.get("digest")
    capabilities = state.get("capabilities", {}) if isinstance(state, dict) else {}
    return {
        "state_file": str(PREP_STATE),
        "state_exists": PREP_STATE.is_file(),
        "updated_at": state.get("updated_at"),
        "signature_matches": signature_matches,
        "capabilities": capabilities,
        "blockers": state.get("blockers", []),
        "prepared_workflows_ready": bool(capabilities) and all(bool((capabilities.get(name) or {}).get("ready")) for name in ["hot", "download", "search", "comments", "watch", "subtitles", "player"]),
    }


def capability_gate(capability: str) -> dict[str, Any]:
    snapshot = health_snapshot()
    prepare_summary = snapshot.get("prepare_state", {})
    capabilities = prepare_summary.get("capabilities", {})
    capability_state = capabilities.get(capability) if isinstance(capabilities, dict) else None
    if not prepare_summary.get("state_exists"):
        return {
            "ready": False,
            "message": f"No prepare-state file found. Run python scripts/bili_prepare.py before using the {capability} workflow.",
            "prepare_summary": prepare_summary,
        }
    if not prepare_summary.get("signature_matches"):
        return {
            "ready": False,
            "message": f"Prepare-state no longer matches the current Bilibili environment. Rerun python scripts/bili_prepare.py before using the {capability} workflow.",
            "prepare_summary": prepare_summary,
        }
    if not isinstance(capability_state, dict) or not capability_state.get("ready"):
        return {
            "ready": False,
            "message": (capability_state or {}).get("message") or f"{capability} is not prepared yet. Run python scripts/bili_prepare.py.",
            "prepare_summary": prepare_summary,
        }
    return {"ready": True, "message": "", "prepare_summary": prepare_summary}
