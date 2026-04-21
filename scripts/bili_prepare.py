#!/usr/bin/env python3
from __future__ import annotations

import json
import os

from bili_core import PREP_STATE, health_snapshot
from prepare_state import default_prepare_state, set_capability, set_phase, write_prepare_state


def prepare_payload(state: dict, snapshot: dict) -> dict:
    capabilities = state.get("capabilities", {})
    blockers = state.get("blockers", [])
    status = "ready" if not blockers else "failed"
    return {
        "success": status == "ready",
        "status": status,
        "state_file": str(PREP_STATE),
        "runtime_signature": state.get("runtime_signature"),
        "phases": state.get("phases", {}),
        "capabilities": capabilities,
        "blockers": blockers,
        "status_snapshot": {
            "read_only_ready": snapshot.get("read_only_ready"),
            "all_ready": snapshot.get("all_ready"),
        },
        "next_actions": ["Preparation passed. You can continue with bili_search.py, bili_comments.py, bili_download.py, bili_watch.py, bili_subtitle.py, or bili_play.py."] if not blockers else blockers,
    }


def main() -> int:
    snapshot = health_snapshot()
    state = default_prepare_state()
    state["runtime_signature"] = snapshot.get("runtime_signature", {})
    blockers: list[str] = []

    ready = bool(snapshot.get("impl_package_exists") and snapshot.get("read_only_ready"))
    set_phase(state, "readiness", "ready" if ready else "failed", snapshot)
    if not ready:
        blockers.append("Bilibili read-only core is not ready. Check bili_impl package installation.")

    for capability in ["hot", "download", "search", "comments", "watch", "subtitles", "player"]:
        set_capability(state, capability, ready, "Read-only workflow is prepared." if ready else "Read-only core is not ready.")
    set_capability(
        state,
        "transcription",
        bool(os.getenv("DASHSCOPE_API_KEY")),
        "DashScope key present." if os.getenv("DASHSCOPE_API_KEY") else "Set DASHSCOPE_API_KEY in the current agent session if transcription is needed.",
    )

    state["blockers"] = blockers
    write_prepare_state(PREP_STATE, state)
    print(json.dumps(prepare_payload(state, health_snapshot()), ensure_ascii=False, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
