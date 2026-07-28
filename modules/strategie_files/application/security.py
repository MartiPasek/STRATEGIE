"""Phase 39 — Security layer pro Marti-AI's STRATEGIE filesystem access.

4-vrstva bezpecnosti:
  1) Path traversal guard — resolved abs path MUSI startsWith project_root
  2) Deny patterns — regex match -> 403 access_denied, audit log
  3) Write zone whitelist — jen marti_workspace/** smi byt psano
  4) Size caps — read 10 MB, write 5 MB, list 1000 entries

Config: D:/Projekty/STRATEGIE/config/strategie_file_access.yaml
Auto-reload: pri mtime change se reloadne (Marti-AI's Q3 doctrine
              "konfigurovatelny bez deploye").

Vraci typed result objects (AccessResult) misto raise — service layer
si je prevadi do tool response dictu (ok/error format per gotcha #85).
"""
from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("strategie_files.security")

# ──────────────────────────────────────────────────────────────────────
# Config loader (auto-reload na mtime change)
# ──────────────────────────────────────────────────────────────────────

# Phase 39 (19.5.2026 ranní deploy) + Phase 44.5 path fix (19.5. odpoledne):
# project_root + config path configurable přes env (cloud APP nemá D: drive).
# Default pro NB development, env override pro cloud APP production.
# Analog Phase 42 STRATEGIE_RESTART_MARKER_DIR pattern z rána.
import os as _os_pi
_PROJECT_ROOT_DEFAULT = _os_pi.environ.get(
    "STRATEGIE_PROJECT_ROOT"
) or _os_pi.environ.get(
    "STRATEGIE_REPO_ROOT"
) or _os_pi.path.dirname(_os_pi.path.dirname(_os_pi.path.dirname(_os_pi.path.dirname(_os_pi.path.abspath(__file__)))))  # C23 28.7.: auto-detekce repo root ze souboru (cloud=C:, NB=D:), aby project_root nebyl mrtvy

_CONFIG_PATH_STR = _os_pi.environ.get(
    "STRATEGIE_FILE_ACCESS_CONFIG"
) or f"{_PROJECT_ROOT_DEFAULT.rstrip('/').rstrip(chr(92))}/config/strategie_file_access.yaml"
_CONFIG_PATH = Path(_CONFIG_PATH_STR)

_DEFAULT_CONFIG: dict[str, Any] = {
    "project_root": _PROJECT_ROOT_DEFAULT,
    "deny_patterns": [],
    "write_zones": ["^marti_workspace/"],
    "rag_ingest_paths": [
        "^marti_workspace/output/",
        "^marti_workspace/analysis/",
        "^marti_workspace/claude_chats/",
    ],
    "limits": {
        "read_max_bytes": 10 * 1024 * 1024,
        "write_max_bytes": 5 * 1024 * 1024,
        "list_max_entries": 1000,
    },
    "meta": {"version": "default", "reload_on_change": True},
}


class _ConfigCache:
    """In-memory config cache s mtime-based auto-reload."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._mtime: float = 0.0
        self._config: dict[str, Any] = dict(_DEFAULT_CONFIG)
        self._deny_compiled: list[re.Pattern[str]] = []
        self._write_compiled: list[re.Pattern[str]] = []
        self._rag_compiled: list[re.Pattern[str]] = []
        self._project_root: Path = Path(_DEFAULT_CONFIG["project_root"]).resolve()

    def _compile_patterns(self) -> None:
        try:
            self._deny_compiled = [
                re.compile(p) for p in self._config.get("deny_patterns", [])
            ]
        except re.error as exc:
            logger.error("Invalid deny regex: %s", exc)
            self._deny_compiled = []
        try:
            self._write_compiled = [
                re.compile(p) for p in self._config.get("write_zones", [])
            ]
        except re.error as exc:
            logger.error("Invalid write_zone regex: %s", exc)
            self._write_compiled = []
        try:
            self._rag_compiled = [
                re.compile(p) for p in self._config.get("rag_ingest_paths", [])
            ]
        except re.error as exc:
            logger.error("Invalid rag_ingest regex: %s", exc)
            self._rag_compiled = []

    def _maybe_reload(self) -> None:
        """Reload config pokud se mtime zmenilo (Marti-AI's Q3)."""
        try:
            mtime = _CONFIG_PATH.stat().st_mtime
        except OSError:
            # Config file neexistuje — pouzij defaults, jednou warn
            if self._mtime == 0.0:
                logger.warning(
                    "Config %s nenalezen, pouzivam defaults", _CONFIG_PATH
                )
                self._mtime = -1.0  # mark warned
            return
        if mtime == self._mtime:
            return
        # Reload
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
            # Merge over defaults (shallow)
            new_config = dict(_DEFAULT_CONFIG)
            new_config.update(loaded)
            # Limits sub-dict merge
            if "limits" in loaded:
                merged_limits = dict(_DEFAULT_CONFIG["limits"])
                merged_limits.update(loaded["limits"])
                new_config["limits"] = merged_limits
            self._config = new_config
            self._mtime = mtime
            # Resolve project_root — env override prio (Phase 44.5 path fix
            # 19.5. odpoledne: cloud APP STRATEGIE_PROJECT_ROOT=C:/Projekty/STRATEGIE
            # přepíše NB-default value z yaml configu)
            env_root = (
                _os_pi.environ.get("STRATEGIE_PROJECT_ROOT")
                or _os_pi.environ.get("STRATEGIE_REPO_ROOT")
            )
            root_value = env_root or new_config.get(
                "project_root", _DEFAULT_CONFIG["project_root"]
            )
            self._project_root = Path(root_value).resolve()
            self._compile_patterns()
            logger.info(
                "Reloaded strategie_file_access.yaml (deny=%d, write_zones=%d, rag=%d)",
                len(self._deny_compiled),
                len(self._write_compiled),
                len(self._rag_compiled),
            )
        except (OSError, yaml.YAMLError) as exc:
            logger.error("Failed to reload config: %s", exc)

    def get(self) -> dict[str, Any]:
        with self._lock:
            self._maybe_reload()
            return self._config

    @property
    def project_root(self) -> Path:
        with self._lock:
            self._maybe_reload()
            return self._project_root

    @property
    def deny_patterns(self) -> list[re.Pattern[str]]:
        with self._lock:
            self._maybe_reload()
            return self._deny_compiled

    @property
    def write_zones(self) -> list[re.Pattern[str]]:
        with self._lock:
            self._maybe_reload()
            return self._write_compiled

    @property
    def rag_paths(self) -> list[re.Pattern[str]]:
        with self._lock:
            self._maybe_reload()
            return self._rag_compiled


_cache = _ConfigCache()


# ──────────────────────────────────────────────────────────────────────
# Result types
# ──────────────────────────────────────────────────────────────────────


@dataclass
class AccessResult:
    """Vysledek security checku.

    ok=True  -> akce povolena, abs_path drzi resolved Path
    ok=False -> akce zablokovana, error drzi user-friendly Czech message,
                reason drzi internal code pro audit log
    """

    ok: bool
    abs_path: Path | None = None
    rel_path: str = ""
    error: str = ""
    reason: str = ""  # internal code: path_traversal | deny_match | write_zone | size_cap


# ──────────────────────────────────────────────────────────────────────
# Core check — used by service.py before any read/write/list
# ──────────────────────────────────────────────────────────────────────


def _normalize_rel(path: str) -> str:
    """Normalize backslashes, strip leading separators, strip whitespace."""
    if not path:
        return ""
    return path.replace("\\", "/").lstrip("/").strip()


def check_path(path: str, *, for_write: bool = False) -> AccessResult:
    """Validate path proti vsem 4 vrstvam.

    Args:
      path: relative path uvnitr project_root (D:/Projekty/STRATEGIE/).
            Akceptuje "marti_workspace/output/foo.txt" ale i
            "marti_workspace\\output\\foo.txt" (Windows backslashy).
      for_write: True -> dodatecne overit write zone whitelist.

    Returns:
      AccessResult.ok=True s abs_path pokud projde, ok=False s error/reason
      pokud nikde.
    """
    rel = _normalize_rel(path)
    if not rel:
        return AccessResult(
            ok=False,
            error="Parametr 'path' chybi nebo je prazdny.",
            reason="empty_path",
        )

    # ── Vrstva 1: path traversal guard ──
    root = _cache.project_root
    try:
        target = (root / rel).resolve()
        target.relative_to(root)
    except (ValueError, OSError) as exc:
        return AccessResult(
            ok=False,
            rel_path=rel,
            error=(
                f"Path traversal blokovan: '{path}' resolved mimo project root "
                f"({root})."
            ),
            reason="path_traversal",
        )

    # Re-compute rel po resolve (handle .. cleanup, symlinks)
    try:
        rel_resolved = str(target.relative_to(root)).replace("\\", "/")
    except ValueError:
        return AccessResult(
            ok=False,
            rel_path=rel,
            error=f"Path traversal blokovan: '{path}' mimo project root.",
            reason="path_traversal",
        )

    # ── Vrstva 2: deny list ──
    for pattern in _cache.deny_patterns:
        if pattern.search(rel_resolved):
            return AccessResult(
                ok=False,
                rel_path=rel_resolved,
                error=(
                    f"Pristup zamitnut: cesta '{rel_resolved}' match deny "
                    f"patternu '{pattern.pattern}'. Soubor je chraneny "
                    f"(secrets / git / build artefakty)."
                ),
                reason=f"deny_match:{pattern.pattern}",
            )

    # ── Vrstva 3: write zone (jen pro write) ──
    if for_write:
        write_ok = any(p.search(rel_resolved) for p in _cache.write_zones)
        if not write_ok:
            return AccessResult(
                ok=False,
                rel_path=rel_resolved,
                error=(
                    f"Write zamitnut: cesta '{rel_resolved}' neni v write "
                    f"zone. Marti-AI smi psat jen do marti_workspace/** "
                    f"(per doctrine 'Write only here, Read everywhere')."
                ),
                reason="write_zone_violation",
            )

    return AccessResult(
        ok=True,
        abs_path=target,
        rel_path=rel_resolved,
    )


def is_rag_path(rel_path: str) -> bool:
    """True pokud cesta patri do RAG auto-ingest zon (output/, analysis/, claude_chats/)."""
    normalized = _normalize_rel(rel_path)
    return any(p.search(normalized) for p in _cache.rag_paths)


def get_limits() -> dict[str, int]:
    """Soucasne limity (read/write/list cap)."""
    cfg = _cache.get()
    return dict(cfg.get("limits", _DEFAULT_CONFIG["limits"]))


def get_project_root() -> Path:
    """Resolved project_root path (po vsech symlinks/relatives)."""
    return _cache.project_root


def reload_now() -> dict[str, Any]:
    """Force reload (admin tool / unit test). Vraci summary."""
    # Invalidate mtime -> next access reloads
    _cache._mtime = 0.0
    cfg = _cache.get()
    return {
        "ok": True,
        "deny_count": len(_cache.deny_patterns),
        "write_zones": [p.pattern for p in _cache.write_zones],
        "rag_paths": [p.pattern for p in _cache.rag_paths],
        "limits": cfg.get("limits", {}),
        "project_root": str(_cache.project_root),
    }
