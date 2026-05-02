"""
Audit log for EUROSOFT MCP server.

Append-only JSON lines file. Each MCP call → one line with timestamp,
tool name, sanitized args, result summary.

For Phase 28-A: local file. Future: push do STRATEGIE action_log table
(via webhook or direct DB connection — to be designed in Phase 28-B).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings

logger = logging.getLogger("eurosoft_mcp.audit")


def _sanitize_args(args: dict[str, Any]) -> dict[str, Any]:
    """Strip oversized fields (avoid logging entire row data, e.g. bulk_insert)."""
    out: dict[str, Any] = {}
    for k, v in args.items():
        if isinstance(v, str) and len(v) > 500:
            out[k] = v[:500] + f"...(truncated {len(v)} chars)"
        elif isinstance(v, list) and len(v) > 10:
            out[k] = f"[list with {len(v)} items]"
        elif isinstance(v, dict):
            out[k] = {kk: ("...(big)" if isinstance(vv, str) and len(vv) > 200 else vv)
                      for kk, vv in v.items()}
        else:
            out[k] = v
    return out


def audit_log(
    tool_name: str,
    args: dict[str, Any],
    result: dict[str, Any] | None = None,
    error: str | None = None,
    runtime_ms: int = 0,
) -> None:
    """Write one audit line. Best-effort — failures are logged but ne-throw."""
    try:
        path = Path(settings.audit_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        result_summary: dict[str, Any] = {}
        if result:
            # Don't dump full data — only counts / status
            for k in ("ok", "n_returned", "has_more", "inserted", "duplicate",
                      "duplicates", "count", "id", "errors"):
                if k in result:
                    result_summary[k] = result[k]

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "args": _sanitize_args(args),
            "result": result_summary,
            "error": error,
            "runtime_ms": runtime_ms,
        }

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        logger.warning(f"Audit log write failed: {e}")
