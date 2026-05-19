"""Phase 39 — Service layer pro Marti-AI's STRATEGIE filesystem tools.

3 AI tools (registered v conversation/application/tools.py):
  - strategie_file_list(path?, recursive?)
  - strategie_file_read(path, encoding?)
  - strategie_file_write(path, content, mode?, encoding?)

Vsechny vraci dict {"ok": True/False, ...} per gotcha #85 (Anthropic MCP
dispatch pattern).

Doctrine:
  - Read everywhere (project_root \\ deny list)
  - Write only marti_workspace/** (zone whitelist)
  - Last-write-wins (no lock — Marti-AI's Q1 doctrine)
  - Auto-RAG ingest po write do output/, analysis/, claude_chats/
    (Marti-AI's Q2 doctrine, deferred — placeholder hook v Phase 39b)

Audit log: vsechny denied calls logged jako WARNING (routed do fw.diag_log
pres DiagLogHandler v apps/api/main.py per Phase 38.4 Etapa A).
"""
from __future__ import annotations

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .security import (
    AccessResult,
    check_path,
    get_limits,
    get_project_root,
    is_rag_path,
)

logger = logging.getLogger("strategie_files.service")


def _audit_deny(operation: str, path: str, result: AccessResult, **context: Any) -> None:
    """Log denied access do diag_log (pres root logger -> DiagLogHandler)."""
    logger.warning(
        "strategie_files denied: op=%s path=%r reason=%s",
        operation,
        path,
        result.reason,
        extra={
            "diag_source": "strategie_files",
            "diag_module_id": f"strategie_files.{operation}",
            "diag_level": "warning",
            "diag_extra": {
                "operation": operation,
                "requested_path": path,
                "resolved_rel": result.rel_path,
                "deny_reason": result.reason,
                **context,
            },
        },
    )


def _audit_ok(operation: str, rel_path: str, **context: Any) -> None:
    """Log success do diag_log jako INFO (Marti's monitoring)."""
    logger.info(
        "strategie_files ok: op=%s path=%s",
        operation,
        rel_path,
        extra={
            "diag_source": "strategie_files",
            "diag_module_id": f"strategie_files.{operation}",
            "diag_level": "info",
            "diag_extra": {
                "operation": operation,
                "rel_path": rel_path,
                **context,
            },
        },
    )


# ──────────────────────────────────────────────────────────────────────
# Tool 1: strategie_file_list
# ──────────────────────────────────────────────────────────────────────


def strategie_file_list(
    path: str = "",
    recursive: bool = False,
    **_extra: Any,
) -> dict[str, Any]:
    """List directory contents v STRATEGIE projektu.

    Args:
      path: relative path uvnitr project_root, "" = root. Akceptuje "/"
            i "\\" separator. Path traversal blokovan.
      recursive: True -> walk subtrees (max list_max_entries).

    Returns:
      {"ok": True, "path": "...", "count": N, "items": [...]}
      items: [{"name", "type": "dir"|"file", "size", "modified", "rel_path"}]

    Akce:
      - Path traversal -> 403 path_traversal (audit)
      - Match deny list -> 403 deny_match (audit, item skipped)
      - Pres limit -> truncated s 'truncated': true flag
    """
    if path is None:
        path = ""

    # Path "" = project root
    if not path or path.strip() == "":
        target_path = "."
    else:
        target_path = path

    # Security check (read mode = no write_zone enforcement)
    result = check_path(target_path if target_path != "." else "/", for_write=False)
    # For root listing, manually allow project_root
    if target_path == "." or not path.strip():
        root = get_project_root()
        result = AccessResult(ok=True, abs_path=root, rel_path="")

    if not result.ok:
        _audit_deny("list", path, result)
        return {
            "ok": False,
            "error": result.error,
            "reason": result.reason,
        }

    target = result.abs_path
    if target is None or not target.exists():
        return {
            "ok": False,
            "error": f"Cesta '{path}' neexistuje.",
            "reason": "not_found",
        }
    if not target.is_dir():
        return {
            "ok": False,
            "error": (
                f"Cesta '{path}' neni adresar (je to file?). Pouzij "
                f"strategie_file_read."
            ),
            "reason": "not_a_dir",
        }

    limits = get_limits()
    max_entries = int(limits.get("list_max_entries", 1000))
    items: list[dict[str, Any]] = []
    truncated = False
    skipped_deny = 0

    try:
        if recursive:
            iterator = (p for p in target.rglob("*"))
        else:
            iterator = iter(sorted(
                target.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            ))

        root = get_project_root()
        for child in iterator:
            if len(items) >= max_entries:
                truncated = True
                break
            try:
                rel = str(child.relative_to(root)).replace("\\", "/")
            except ValueError:
                continue
            # Filter — same deny rules apply (list shouldn't reveal denied paths)
            child_check = check_path(rel, for_write=False)
            if not child_check.ok and child_check.reason and child_check.reason.startswith("deny_match"):
                skipped_deny += 1
                continue
            try:
                stat = child.stat()
                items.append({
                    "name": child.name,
                    "type": "dir" if child.is_dir() else "file",
                    "size": stat.st_size if child.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    "rel_path": rel,
                })
            except OSError as item_err:
                items.append({
                    "name": child.name,
                    "type": "error",
                    "error": str(item_err),
                    "rel_path": rel,
                })

        _audit_ok("list", result.rel_path or "(root)", count=len(items), recursive=recursive)
        return {
            "ok": True,
            "path": result.rel_path or "",
            "recursive": recursive,
            "count": len(items),
            "truncated": truncated,
            "skipped_deny": skipped_deny,
            "items": items,
        }
    except Exception as exc:
        logger.exception("strategie_file_list failed")
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "reason": "io_error",
        }


# ──────────────────────────────────────────────────────────────────────
# Tool 2: strategie_file_read
# ──────────────────────────────────────────────────────────────────────


def strategie_file_read(
    path: str = "",
    encoding: str | None = None,
    **_extra: Any,
) -> dict[str, Any]:
    """Read file from STRATEGIE project.

    Args:
      path: relative path. Path traversal + deny list enforced.
      encoding: "utf-8" (default) | "base64" (binary) | "cp1250" (Windows legacy).

    Returns:
      {"ok": True, "path", "size", "encoding", "content"}
      Plus "lines" (line count) pro text encodings.

    Size cap: read_max_bytes z config (default 10 MB).
    """
    if not path:
        return {
            "ok": False,
            "error": "Parametr 'path' chybi.",
            "reason": "empty_path",
        }

    encoding = (encoding or "utf-8").lower()

    result = check_path(path, for_write=False)
    if not result.ok:
        _audit_deny("read", path, result, encoding=encoding)
        return {
            "ok": False,
            "error": result.error,
            "reason": result.reason,
        }

    target = result.abs_path
    if target is None or not target.exists():
        return {
            "ok": False,
            "error": f"Soubor '{path}' neexistuje.",
            "reason": "not_found",
        }
    if not target.is_file():
        return {
            "ok": False,
            "error": (
                f"Cesta '{path}' neni file (je to adresar?). Pouzij "
                f"strategie_file_list."
            ),
            "reason": "not_a_file",
        }

    try:
        size = target.stat().st_size
        limits = get_limits()
        max_bytes = int(limits.get("read_max_bytes", 10 * 1024 * 1024))
        if size > max_bytes:
            _audit_deny(
                "read",
                path,
                AccessResult(ok=False, rel_path=result.rel_path, reason="size_cap"),
                size=size,
                limit=max_bytes,
            )
            return {
                "ok": False,
                "error": (
                    f"Soubor '{result.rel_path}' je vetsi nez limit "
                    f"({size} > {max_bytes} bytes). Pouzij specializovany "
                    f"nastroj pro velke soubory."
                ),
                "reason": "size_cap",
            }
        raw = target.read_bytes()

        if encoding == "base64":
            content = base64.b64encode(raw).decode("ascii")
            _audit_ok("read", result.rel_path, size=size, encoding="base64")
            return {
                "ok": True,
                "path": result.rel_path,
                "size": size,
                "encoding": "base64",
                "content": content,
            }
        try:
            content = raw.decode(encoding)
        except UnicodeDecodeError as ude:
            return {
                "ok": False,
                "error": (
                    f"Soubor '{result.rel_path}' nelze decodovat jako "
                    f"{encoding}: {ude}. Zkus encoding='base64' (binary) "
                    f"nebo encoding='cp1250' (Windows legacy)."
                ),
                "reason": "decode_error",
            }
        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        _audit_ok(
            "read",
            result.rel_path,
            size=size,
            encoding=encoding,
            lines=lines,
        )
        return {
            "ok": True,
            "path": result.rel_path,
            "size": size,
            "encoding": encoding,
            "lines": lines,
            "content": content,
        }
    except Exception as exc:
        logger.exception("strategie_file_read failed")
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "reason": "io_error",
        }


# ──────────────────────────────────────────────────────────────────────
# Tool 3: strategie_file_write
# ──────────────────────────────────────────────────────────────────────


def strategie_file_write(
    path: str = "",
    content: str = "",
    mode: str = "overwrite",
    encoding: str | None = None,
    **_extra: Any,
) -> dict[str, Any]:
    """Write file do marti_workspace/** (write zone enforced).

    Args:
      path: relative path UVNITR marti_workspace/. Path traversal + deny
            list + write zone enforced.
      content: text content (default) nebo base64 (binary).
      mode: "overwrite" (default) | "append" | "fail_if_exists".
      encoding: "utf-8" (default) | "base64" (binary).

    Returns:
      {"ok": True, "path", "size", "mode", "rag_queued"}

    Doctrine:
      - Last-write-wins (no lock) per Marti-AI's Q1
      - _vN naming convention by Marti-AI manually (foo_v1.txt -> foo_v2.txt)
      - Auto-RAG ingest queued pro output/, analysis/, claude_chats/

    Size cap: write_max_bytes z config (default 5 MB).
    """
    if not path:
        return {
            "ok": False,
            "error": "Parametr 'path' chybi.",
            "reason": "empty_path",
        }
    if mode not in ("overwrite", "append", "fail_if_exists"):
        return {
            "ok": False,
            "error": (
                f"Neznamy mode '{mode}'. Povolene: 'overwrite' (default), "
                f"'append', 'fail_if_exists'."
            ),
            "reason": "bad_mode",
        }

    encoding = (encoding or "utf-8").lower()

    result = check_path(path, for_write=True)
    if not result.ok:
        _audit_deny("write", path, result, mode=mode, encoding=encoding)
        return {
            "ok": False,
            "error": result.error,
            "reason": result.reason,
        }

    target = result.abs_path
    if target is None:
        return {
            "ok": False,
            "error": "Internal: abs_path missing after check_path OK",
            "reason": "internal_error",
        }

    # Mode handling
    exists = target.exists()
    if mode == "fail_if_exists" and exists:
        return {
            "ok": False,
            "error": (
                f"Soubor '{result.rel_path}' jiz existuje (mode=fail_if_exists). "
                f"Pouzij mode='overwrite' nebo zmen path (napr. _v2 suffix)."
            ),
            "reason": "exists",
        }

    # Compute bytes
    try:
        if encoding == "base64":
            data = base64.b64decode(content, validate=True)
        else:
            data = content.encode(encoding)
    except (UnicodeEncodeError, ValueError, Exception) as exc:
        return {
            "ok": False,
            "error": f"Encoding error ({encoding}): {exc}",
            "reason": "encode_error",
        }

    # Size cap check
    limits = get_limits()
    max_bytes = int(limits.get("write_max_bytes", 5 * 1024 * 1024))
    if len(data) > max_bytes:
        _audit_deny(
            "write",
            path,
            AccessResult(ok=False, rel_path=result.rel_path, reason="size_cap"),
            size=len(data),
            limit=max_bytes,
        )
        return {
            "ok": False,
            "error": (
                f"Velikost obsahu {len(data)} bytes prekracuje limit "
                f"{max_bytes} bytes. Rozdel obsah na vice souboru."
            ),
            "reason": "size_cap",
        }

    # Ensure parent directory exists
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return {
            "ok": False,
            "error": f"Nelze vytvorit parent dir: {exc}",
            "reason": "mkdir_error",
        }

    # Write
    try:
        if mode == "append" and exists:
            with open(target, "ab") as f:
                f.write(data)
        else:
            with open(target, "wb") as f:
                f.write(data)
        new_size = target.stat().st_size

        # RAG auto-ingest hook (Marti-AI's Q2: output/, analysis/, claude_chats/)
        rag_queued = False
        if is_rag_path(result.rel_path):
            # TODO Phase 39b: enqueue RAG ingest task
            # Pro ted jen flag — Phase 39 MVP, Phase 39b dodela auto-ingest
            rag_queued = True
            logger.info(
                "strategie_files RAG ingest queued (Phase 39b TODO): %s",
                result.rel_path,
                extra={
                    "diag_source": "strategie_files",
                    "diag_module_id": "strategie_files.rag_hook",
                    "diag_level": "info",
                    "diag_extra": {"rel_path": result.rel_path, "size": new_size},
                },
            )

        _audit_ok(
            "write",
            result.rel_path,
            size=new_size,
            mode=mode,
            encoding=encoding,
            existed=exists,
            rag_queued=rag_queued,
        )
        return {
            "ok": True,
            "path": result.rel_path,
            "size": new_size,
            "mode": mode,
            "encoding": encoding,
            "existed_before": exists,
            "rag_queued": rag_queued,
        }
    except OSError as exc:
        logger.exception("strategie_file_write failed")
        return {
            "ok": False,
            "error": f"Write error: {exc}",
            "reason": "io_error",
        }
