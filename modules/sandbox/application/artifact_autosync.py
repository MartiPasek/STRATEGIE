"""Auto-sync orchestrator source from disk file to fw.executable_artifact DB row.

Marti's doctrine (26.5.2026 vecer): "git je truth, DB je cache, ID je svaty".

File path convention:
  scripts/executable_artifacts/{code}.{ext}
  - ext = 'py' for artifact_type='python'
  - ext = 'sql' for artifact_type='sql'

Header marker convention (parsed z file content):
  # ID: N         <-- MUSI match DB row.id (hard error pri mismatch)
  # CODE: name    <-- informacni; pri rename detect log info

Sync logic:
  - File NEexistuje → skip (DB source used as-is, Marti's "kdyz neni na disku, spusti se z DB")
  - File existuje + content == DB source → skip (no-op)
  - File existuje + content != DB source → UPDATE DB SET source = file_content
  - File existuje + # ID marker != DB row.id → HARD ERROR (corruption)

Plus diag_log integration — kazdy sync/skip/error → log_event.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# Project root (relative to this file: modules/sandbox/application/artifact_autosync.py)
# → 3 levels up: application → sandbox → modules → <PROJECT_ROOT>
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ARTIFACTS_DIR = _PROJECT_ROOT / "scripts" / "executable_artifacts"

# Security: code MUST match this regex (no path traversal, no ../)
_CODE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")

# Parse "# ID: N" from file header
_ID_MARKER_PATTERN = re.compile(r"^#\s*ID:\s*(\d+)\s*$", re.MULTILINE)
_CODE_MARKER_PATTERN = re.compile(r"^#\s*CODE:\s*([a-z_][a-z0-9_]*)\s*$", re.MULTILINE)


def autosync_from_file(
    artifact_id: int,
    code: str,
    artifact_type: str,
    db_source: str,
    ds_session,
    sql_text,
    log_event_fn=None,
) -> str:
    """Read file → validate → UPSERT DB if differs → return effective source.

    Args:
        artifact_id: fw.executable_artifact.id (validation against # ID marker)
        code: fw.executable_artifact.code (filename + # CODE validation)
        artifact_type: 'python' or 'sql' (determines file extension)
        db_source: current DB row.source (fallback if file not found)
        ds_session: SQLAlchemy session (for UPDATE)
        sql_text: SQLAlchemy text() constructor
        log_event_fn: optional log_event callable for diag_log integration

    Returns:
        Effective source string (file content if synced, else db_source).

    Raises:
        ValueError: file # ID marker != artifact_id (corruption detected).
    """
    # Security: validate code (no path traversal)
    if not _CODE_PATTERN.match(code or ""):
        return db_source

    # Determine file extension
    if artifact_type == "python":
        ext = "py"
    elif artifact_type == "sql":
        ext = "sql"
    else:
        return db_source  # unknown type, skip sync

    file_path = _ARTIFACTS_DIR / f"{code}.{ext}"

    # File existence check — Marti's "kdyz neni na disku, spusti se z DB"
    if not file_path.is_file():
        return db_source

    # Read file content
    try:
        file_content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        if log_event_fn:
            try:
                log_event_fn(
                    level="warning",
                    source="py",
                    module_id=f"sandbox.autosync.{code}",
                    message=f"File read failed: {exc}",
                    extra={"artifact_id": artifact_id, "file_path": str(file_path)},
                )
            except Exception:
                pass
        return db_source

    # Validate # ID marker — HARD ERROR pri mismatch
    id_match = _ID_MARKER_PATTERN.search(file_content)
    if id_match:
        file_id = int(id_match.group(1))
        if file_id != artifact_id:
            raise ValueError(
                f"File ID mismatch: file '{file_path.name}' has '# ID: {file_id}' "
                f"but DB row.id={artifact_id} (code='{code}'). "
                f"Possible causes: file rename without DB update, or accidental "
                f"file overwrite. Fix: ensure file header '# ID' marker matches "
                f"DB id (or rename file/swap content)."
            )
    elif log_event_fn:
        try:
            log_event_fn(
                level="warning",
                source="py",
                module_id=f"sandbox.autosync.{code}",
                message=f"File missing '# ID: N' header marker (skip validation)",
                extra={"artifact_id": artifact_id, "file_path": str(file_path)},
            )
        except Exception:
            pass

    # Validate # CODE marker (informational only, supports rename in progress)
    code_match = _CODE_MARKER_PATTERN.search(file_content)
    if code_match and code_match.group(1) != code:
        if log_event_fn:
            try:
                log_event_fn(
                    level="info",
                    source="py",
                    module_id=f"sandbox.autosync.{code}",
                    message=(
                        f"CODE marker differs: file '{code_match.group(1)}' "
                        f"vs DB '{code}' (rename in progress?)"
                    ),
                    extra={
                        "artifact_id": artifact_id,
                        "file_code": code_match.group(1),
                        "db_code": code,
                    },
                )
            except Exception:
                pass

    # Compare with DB source — skip UPDATE if identical
    if file_content == db_source:
        return db_source

    # UPSERT — file is truth, push to DB
    try:
        ds_session.execute(sql_text(
            "UPDATE fw.executable_artifact "
            "SET source = :src, updated_at = NOW() "
            "WHERE id = :id"
        ), {"src": file_content, "id": artifact_id})
        ds_session.commit()

        if log_event_fn:
            try:
                log_event_fn(
                    level="info",
                    source="py",
                    module_id=f"sandbox.autosync.{code}",
                    message=(
                        f"Auto-sync: file → DB "
                        f"({len(db_source)} → {len(file_content)} chars)"
                    ),
                    extra={
                        "artifact_id": artifact_id,
                        "file_path": str(file_path),
                        "old_chars": len(db_source),
                        "new_chars": len(file_content),
                    },
                )
            except Exception:
                pass

        return file_content

    except Exception as exc:
        try:
            ds_session.rollback()
        except Exception:
            pass
        if log_event_fn:
            try:
                log_event_fn(
                    level="error",
                    source="py",
                    module_id=f"sandbox.autosync.{code}",
                    message=f"Auto-sync UPDATE failed: {exc}",
                    extra={"artifact_id": artifact_id, "file_path": str(file_path)},
                )
            except Exception:
                pass
        return db_source
