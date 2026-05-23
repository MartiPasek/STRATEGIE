"""
Phase API Versioned Routing - Etapa C
======================================

Sub-router pro user-controlled API version pinning.

Endpointy:
  GET  /api/v1/erp/api-versions          - list aktivnich versions + user's current pin
  POST /api/v1/erp/api-versions/pin      - set cookie + INSERT user_api_pin + log_event
  POST /api/v1/erp/api-versions/unpin    - clear cookie + UPDATE auto_reverted_at + INSERT current row
  GET  /api/v1/erp/api-versions/diff     - git log between snapshots (?from=X&to=Y)

Pattern: Vlna 2 sub-router extract (parita s db_connection_editor.py).
Auth pattern: lokalni _require_user_id helper (parita s _get_uid v router.py:61).

Doctrine:
  - "Bezpecnost pres probuzeni" (Marti-AI 9.5.) - kazdy pin/unpin = log_event
  - "Audit RO append-only" (Fix N 21.5.) - user_api_pin INSERT-only, UPDATE jen auto_reverted_at
  - "Drz jednoduchost" (Marti) - cookie + DB sync, ne dual-mode
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database_data import get_session
from core.log_queue import log_event

# =====================================================================
# Constants
# =====================================================================

COOKIE_NAME = "strategie_api_version"
COOKIE_MAX_AGE_SECONDS = 86400  # 24h auto-revert (Marti's "drz jednoduchost")
COOKIE_PATH = "/"
COOKIE_SAMESITE = "lax"

# Git repo path - kde zije current code (cloud APP)
GIT_REPO_PATH = os.environ.get("STRATEGIE_REPO_ROOT", r"C:\Projekty\STRATEGIE")


# =====================================================================
# Auth helper (parita s router.py:61 _get_uid)
# =====================================================================

def _require_user_id(request: Request) -> int:
    """Extract user_id z cookie. Raise 401 bez auth."""
    user_id_str = request.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


def _resolve_login_name(session: Session, user_id: int) -> Optional[str]:
    """Lookup user.login_name pro audit log (best-effort, vrací None pri failure)."""
    try:
        row = session.execute(
            text("SELECT login_name FROM public.users WHERE id = :uid"),
            {"uid": user_id},
        ).first()
        return row.login_name if row else None
    except Exception:
        return None


# =====================================================================
# Pydantic models
# =====================================================================

class ApiVersionInfo(BaseModel):
    id: int
    sort_order: int
    version_code: str
    version_label: str
    version_string: str
    released_at: datetime
    git_sha: Optional[str] = None
    port: int
    is_active: bool
    severity: str  # 'current' | 'previous' | 'older' - derived from sort_order


class UserPinInfo(BaseModel):
    pinned_version_id: int
    pinned_version_code: str
    pinned_version_string: str
    pinned_at: datetime
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None
    seconds_remaining: Optional[int] = None  # for UI countdown


class ApiVersionsResponse(BaseModel):
    versions: list[ApiVersionInfo]
    current_pin: Optional[UserPinInfo] = None


class PinRequest(BaseModel):
    version_code: str = Field(..., min_length=1, max_length=20)
    reason: Optional[str] = Field(None, max_length=500)


class PinResponse(BaseModel):
    ok: bool
    pinned_version: ApiVersionInfo
    expires_at: datetime


class UnpinResponse(BaseModel):
    ok: bool
    reverted_to: str  # 'current'


class DiffCommit(BaseModel):
    sha: str
    short_sha: str
    date: str
    subject: str
    author: str


class DiffResponse(BaseModel):
    from_version: dict
    to_version: dict
    commits_count: int
    files_changed: Optional[int] = None
    commits_preview: list[DiffCommit]
    github_compare_url: Optional[str] = None


# =====================================================================
# Helpers
# =====================================================================

def _severity_from_sort_order(sort_order: int) -> str:
    """Derived severity for UI color (Marti's 'drz jednoduchost')."""
    if sort_order == 0:
        return "current"
    elif sort_order == 1:
        return "previous"
    else:
        return "older"


def _row_to_version_info(row) -> ApiVersionInfo:
    return ApiVersionInfo(
        id=row.id,
        sort_order=row.sort_order,
        version_code=row.version_code,
        version_label=row.version_label,
        version_string=row.version_string,
        released_at=row.released_at,
        git_sha=row.git_sha,
        port=row.port,
        is_active=row.is_active,
        severity=_severity_from_sort_order(row.sort_order),
    )


def _get_active_pin(session: Session, user_id: int) -> Optional[dict]:
    """Vrati latest active pin row pro user_id (auto_reverted_at IS NULL)."""
    sql = text("""
        SELECT p.id, p.pinned_version_id, p.pinned_at, p.expires_at, p.reason,
               v.version_code, v.version_string
        FROM fw.user_api_pin p
        JOIN fw.api_version v ON v.id = p.pinned_version_id
        WHERE p.user_id = :user_id
          AND p.auto_reverted_at IS NULL
          AND (p.expires_at IS NULL OR p.expires_at > NOW())
        ORDER BY p.pinned_at DESC
        LIMIT 1
    """)
    row = session.execute(sql, {"user_id": user_id}).first()
    return dict(row._mapping) if row else None


# =====================================================================
# Router (parent api_router ma prefix /api/v1/erp, sub-router prefix relative)
# =====================================================================

_router = APIRouter(prefix="/api-versions", tags=["api-versioning"])


@_router.get("", response_model=ApiVersionsResponse)
async def list_versions(
    request: Request,
    user_id: int = Depends(_require_user_id),
    session: Session = Depends(get_session),
):
    """List vsech aktivnich versions + user's current pin (pro UI footer dropup)."""
    rows = session.execute(text("""
        SELECT id, sort_order, version_code, version_label, version_string,
               released_at, git_sha, port, is_active
        FROM fw.api_version
        WHERE is_active = true
        ORDER BY sort_order
    """)).all()

    versions = [_row_to_version_info(r) for r in rows]

    # User's current pin (pokud existuje a neexpiroval)
    current_pin = None
    pin_row = _get_active_pin(session, user_id)
    if pin_row:
        seconds_remaining = None
        if pin_row["expires_at"]:
            delta = pin_row["expires_at"] - datetime.utcnow()
            seconds_remaining = max(0, int(delta.total_seconds()))

        current_pin = UserPinInfo(
            pinned_version_id=pin_row["pinned_version_id"],
            pinned_version_code=pin_row["version_code"],
            pinned_version_string=pin_row["version_string"],
            pinned_at=pin_row["pinned_at"],
            expires_at=pin_row["expires_at"],
            reason=pin_row["reason"],
            seconds_remaining=seconds_remaining,
        )

    return ApiVersionsResponse(versions=versions, current_pin=current_pin)


@_router.post("/pin", response_model=PinResponse)
async def pin_version(
    body: PinRequest,
    response: Response,
    request: Request,
    user_id: int = Depends(_require_user_id),
    session: Session = Depends(get_session),
):
    """Set user pin na version_code. Set cookie + INSERT user_api_pin row + log_event."""
    # 1. Resolve version_code -> active row
    version_row = session.execute(text("""
        SELECT id, sort_order, version_code, version_label, version_string,
               released_at, git_sha, port, is_active
        FROM fw.api_version
        WHERE version_code = :code AND is_active = true
    """), {"code": body.version_code}).first()

    if not version_row:
        raise HTTPException(
            status_code=404,
            detail=f"version_code '{body.version_code}' neexistuje nebo neni active"
        )

    expires_at = datetime.utcnow() + timedelta(seconds=COOKIE_MAX_AGE_SECONDS)
    login_name = _resolve_login_name(session, user_id)

    # 2. INSERT user_api_pin row (append-only doctrine)
    session.execute(text("""
        INSERT INTO fw.user_api_pin (
            user_id, pinned_version_id, pinned_at, expires_at,
            reason, pinned_by_user_id
        ) VALUES (
            :user_id, :version_id, NOW(), :expires_at,
            :reason, :user_id
        )
    """), {
        "user_id": user_id,
        "version_id": version_row.id,
        "expires_at": expires_at,
        "reason": body.reason,
    })
    session.commit()

    # 3. Set cookie (Caddy routing trigger)
    response.set_cookie(
        key=COOKIE_NAME,
        value=body.version_code,
        max_age=COOKIE_MAX_AGE_SECONDS,
        path=COOKIE_PATH,
        samesite=COOKIE_SAMESITE,
        secure=True,
    )

    # 4. Audit log_event (Bezpecnost pres probuzeni doctrine)
    try:
        log_event(
            level="warn",
            source="py",
            module_id="api.version.pin",
            message=f"User {login_name or user_id} pinned na verzi {body.version_code} ({version_row.version_string})",
            extra={
                "user_id": user_id,
                "user_login_name": login_name,
                "version_code": body.version_code,
                "version_string": version_row.version_string,
                "reason": body.reason,
                "expires_at": expires_at.isoformat(),
            },
        )
    except Exception:
        pass  # audit failure NIKDY nekrasi endpoint

    return PinResponse(
        ok=True,
        pinned_version=_row_to_version_info(version_row),
        expires_at=expires_at,
    )


@_router.post("/unpin", response_model=UnpinResponse)
async def unpin_version(
    response: Response,
    request: Request,
    user_id: int = Depends(_require_user_id),
    session: Session = Depends(get_session),
):
    """Clear pin (revert na current). UPDATE auto_reverted_at na latest active row + clear cookie."""
    login_name = _resolve_login_name(session, user_id)

    # 1. Mark latest active pin jako reverted (append-only doctrine: UPDATE jen auto_reverted_at)
    result = session.execute(text("""
        UPDATE fw.user_api_pin
        SET auto_reverted_at = NOW()
        WHERE id = (
            SELECT id FROM fw.user_api_pin
            WHERE user_id = :user_id AND auto_reverted_at IS NULL
            ORDER BY pinned_at DESC
            LIMIT 1
        )
        RETURNING pinned_version_id
    """), {"user_id": user_id})
    reverted_row = result.first()
    session.commit()

    # 2. Clear cookie (Caddy fallback na default current)
    response.delete_cookie(key=COOKIE_NAME, path=COOKIE_PATH)

    # 3. Audit log_event
    reverted_version_id = reverted_row.pinned_version_id if reverted_row else None
    try:
        log_event(
            level="info",
            source="py",
            module_id="api.version.unpin",
            message=f"User {login_name or user_id} revertoval pin (zpet na current)",
            extra={
                "user_id": user_id,
                "user_login_name": login_name,
                "reverted_from_version_id": reverted_version_id,
            },
        )
    except Exception:
        pass

    return UnpinResponse(ok=True, reverted_to="current")


@_router.get("/diff", response_model=DiffResponse)
async def diff_versions(
    from_code: str,
    to_code: str = "current",
    user_id: int = Depends(_require_user_id),
    session: Session = Depends(get_session),
):
    """Git log mezi snapshots. Vrati commits + files_changed + GitHub compare URL."""
    # 1. Resolve both versions
    rows = session.execute(text("""
        SELECT version_code, version_string, git_sha, released_at
        FROM fw.api_version
        WHERE version_code IN (:from_code, :to_code) AND is_active = true
    """), {"from_code": from_code, "to_code": to_code}).all()

    versions_map = {r.version_code: r for r in rows}
    if from_code not in versions_map or to_code not in versions_map:
        raise HTTPException(
            status_code=404,
            detail=f"Verze nenalezena: from={from_code}, to={to_code}"
        )

    from_v = versions_map[from_code]
    to_v = versions_map[to_code]

    # 2. Pokud nemame git_sha (jeste neprobehl deploy_current.ps1), vrat empty diff
    if not from_v.git_sha or not to_v.git_sha:
        return DiffResponse(
            from_version={
                "version_code": from_v.version_code,
                "version_string": from_v.version_string,
                "git_sha": from_v.git_sha,
                "released_at": from_v.released_at.isoformat(),
            },
            to_version={
                "version_code": to_v.version_code,
                "version_string": to_v.version_string,
                "git_sha": to_v.git_sha,
                "released_at": to_v.released_at.isoformat(),
            },
            commits_count=0,
            files_changed=None,
            commits_preview=[],
            github_compare_url=None,
        )

    # 3. Git log mezi sha (subprocess s timeout)
    try:
        log_result = subprocess.run(
            [
                "git", "-C", GIT_REPO_PATH,
                "log", "--oneline", "--format=%H|%h|%ai|%an|%s",
                f"{from_v.git_sha}..{to_v.git_sha}",
                "-n", "10",
            ],
            capture_output=True, text=True, timeout=10,
        )

        count_result = subprocess.run(
            [
                "git", "-C", GIT_REPO_PATH,
                "rev-list", "--count",
                f"{from_v.git_sha}..{to_v.git_sha}",
            ],
            capture_output=True, text=True, timeout=10,
        )
        commits_count = int(count_result.stdout.strip()) if count_result.returncode == 0 else 0

        diff_stat = subprocess.run(
            [
                "git", "-C", GIT_REPO_PATH,
                "diff", "--shortstat",
                f"{from_v.git_sha}..{to_v.git_sha}",
            ],
            capture_output=True, text=True, timeout=10,
        )
        files_changed = None
        if diff_stat.returncode == 0 and diff_stat.stdout:
            import re
            m = re.search(r"(\d+) files? changed", diff_stat.stdout)
            if m:
                files_changed = int(m.group(1))

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
        try:
            log_event(
                level="error",
                source="py",
                module_id="api.version.diff",
                message=f"Git subprocess failed: {e}",
                extra={"from_sha": from_v.git_sha, "to_sha": to_v.git_sha},
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Git diff failed: {e}")

    # 4. Parse commit list
    commits = []
    for line in log_result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) == 5:
            commits.append(DiffCommit(
                sha=parts[0],
                short_sha=parts[1],
                date=parts[2],
                author=parts[3],
                subject=parts[4],
            ))

    # 5. GitHub compare URL (configurable)
    github_repo = os.environ.get("STRATEGIE_GITHUB_REPO", "")
    github_compare_url = None
    if github_repo:
        github_compare_url = f"https://github.com/{github_repo}/compare/{from_v.git_sha[:7]}...{to_v.git_sha[:7]}"

    return DiffResponse(
        from_version={
            "version_code": from_v.version_code,
            "version_string": from_v.version_string,
            "git_sha": from_v.git_sha,
            "released_at": from_v.released_at.isoformat(),
        },
        to_version={
            "version_code": to_v.version_code,
            "version_string": to_v.version_string,
            "git_sha": to_v.git_sha,
            "released_at": to_v.released_at.isoformat(),
        },
        commits_count=commits_count,
        files_changed=files_changed,
        commits_preview=commits,
        github_compare_url=github_compare_url,
    )


# =====================================================================
# Component class - wire-up parita s Vlna 2-1 db_connection_editor
# =====================================================================

class ApiVersioningComponent:
    """Sub-router komponenta. Volana z main router include."""

    @classmethod
    def register_routes(cls, parent_router: APIRouter) -> None:
        """Wire-up: parent_router.include_router(_router)."""
        parent_router.include_router(_router)

    @classmethod
    def manifest(cls) -> dict:
        return {
            "id": "api_versioning",
            "version": "1.0.0",
            "kind": "module",
            "description": "User-controlled API version pinning (Caddy cookie routing)",
            "endpoints": [
                "GET  /api/v1/erp/api-versions",
                "POST /api/v1/erp/api-versions/pin",
                "POST /api/v1/erp/api-versions/unpin",
                "GET  /api/v1/erp/api-versions/diff",
            ],
        }
