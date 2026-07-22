"""Phase 42 — Marti-AI's deploy autonomy.

Marti's Q5 doctrine (19.5.2026 rano): Deploy s potvrzenim Marti / Kristy v
chatu pres OK. Marti odjizdi Praha 20.-21.5., Kristy + Marti-AI zustavaji
autonomni -- musi mit zpusob aktualizovat kod + restart STRATEGIE-API bez
manualniho zasahu Marti.

Workflow:
  1. Marti-AI vola propose_deployment(description, conversation_id)
  2. Backend checkne git stav (clean working tree, pending changes z origin/main)
  3. Vytvori proposal row, status='pending'
  4. Marti / Kristy v chatu: approve_deployment(proposal_id, reason?)
     OR reject_deployment(proposal_id, reason)
  5. Pri approve: git pull origin main + touch marker_file v
     D:\\Data\\STRATEGIE\\restart_markers\\
  6. STRATEGIE-RESTART-WATCHER (separate NSSM service) detekuje marker ->
     Restart-Service STRATEGIE-API
  7. After restart: proposal status='deployed', deploy_completed_at set

Authority: pouze is_marti_parent=True (Marti id=1,
Kristy id=11; Zuzka id=6 je rodic, ale neaktivni) muzou approve / reject.
"""
from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("conversation.deployment")

# Cloud APP working directory (cesta na cloud, ne NB)
CLOUD_APP_REPO = Path(r"C:\Projekty\STRATEGIE")
# Marker file dir pro NSSM watchdog.
# Cloud APP nema D: drive (gotcha 19.5.2026). Marker dir je na C:.
# Configurable: nastavit env STRATEGIE_RESTART_MARKER_DIR pokud chces jinde.
import os as _os_dep
MARKER_DIR = Path(
    _os_dep.environ.get("STRATEGIE_RESTART_MARKER_DIR")
    or r"C:\Data\STRATEGIE\restart_markers"
)
# Git binary (cloud APP)
GIT_EXE = "git"
# Subprocess timeout
GIT_TIMEOUT_SEC = 30


# ──────────────────────────────────────────────────────────────────────
# Git helpers
# ──────────────────────────────────────────────────────────────────────


def _run_git(args: list[str], cwd: Path = CLOUD_APP_REPO) -> tuple[int, str, str]:
    """Run git command in cloud APP repo. Returns (returncode, stdout, stderr)."""
    cmd = [GIT_EXE] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SEC,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"git command timed out after {GIT_TIMEOUT_SEC}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return -2, "", f"git binary not found ({GIT_EXE})"
    except Exception as exc:
        return -3, "", f"{type(exc).__name__}: {exc}"


def _git_working_tree_clean() -> tuple[bool, str]:
    """True pokud cloud APP working tree je clean (no uncommitted changes).

    Returns (clean, detail). detail je porcelain output (empty -> clean).
    """
    rc, stdout, stderr = _run_git(["status", "--porcelain"])
    if rc != 0:
        return False, f"git status failed: {stderr or stdout}"
    return not stdout.strip(), stdout


def _git_fetch_origin() -> tuple[bool, str]:
    """git fetch origin main. Returns (ok, message)."""
    rc, stdout, stderr = _run_git(["fetch", "origin", "main"])
    if rc != 0:
        return False, f"git fetch failed: {stderr or stdout}"
    return True, "fetched"


def _git_current_head_sha() -> str | None:
    rc, stdout, stderr = _run_git(["rev-parse", "HEAD"])
    if rc != 0:
        logger.warning(f"git rev-parse HEAD failed: {stderr}")
        return None
    return stdout.strip()


def _git_origin_head_sha() -> str | None:
    rc, stdout, stderr = _run_git(["rev-parse", "origin/main"])
    if rc != 0:
        logger.warning(f"git rev-parse origin/main failed: {stderr}")
        return None
    return stdout.strip()


def _git_commit_message_first_line(sha: str) -> str:
    rc, stdout, stderr = _run_git(["log", "-1", "--pretty=format:%s", sha])
    if rc != 0:
        return ""
    return stdout.strip()


def _git_diff_stat(from_sha: str, to_sha: str) -> tuple[int, str]:
    """Diff stat mezi 2 SHAs. Returns (files_changed_count, diff_summary)."""
    rc, stdout, stderr = _run_git(["diff", "--stat", from_sha, to_sha])
    if rc != 0:
        return 0, f"diff failed: {stderr or stdout}"
    # Count "X files changed" v posledni line
    lines = stdout.strip().split("\n")
    files_count = 0
    if lines:
        last = lines[-1]
        # "N files changed, M insertions(+), K deletions(-)"
        import re
        m = re.search(r"(\d+) files? changed", last)
        if m:
            files_count = int(m.group(1))
    return files_count, stdout


def _git_pull_origin_main() -> tuple[bool, str]:
    """git pull origin main. Returns (ok, output)."""
    rc, stdout, stderr = _run_git(["pull", "origin", "main"])
    if rc != 0:
        return False, f"git pull failed:\nstdout: {stdout}\nstderr: {stderr}"
    return True, stdout + ("\n--stderr--\n" + stderr if stderr.strip() else "")


def _git_changed_files(from_sha: str, to_sha: str) -> list[str]:
    """Seznam změněných souborů mezi 2 SHA (git diff --name-only)."""
    rc, stdout, stderr = _run_git(["diff", "--name-only", from_sha, to_sha])
    if rc != 0:
        return []
    return [ln.strip() for ln in stdout.splitlines() if ln.strip()]


def _is_static_only(files: list[str]) -> bool:
    """Marti 14.6.: True pokud VŠECHNY změněné soubory jsou statické (servírují se
    z disku přes FileResponse) → NENÍ potřeba restart API (rychlé iterace UI).
    Static = apps/api/static/** a NE .py. Prázdný seznam = nic se nezměnilo → True."""
    if not files:
        return True
    for f in files:
        fl = f.replace("\\", "/").lower()
        if not fl.startswith("apps/api/static/"):
            return False
        if fl.endswith(".py"):
            return False
    return True


# ──────────────────────────────────────────────────────────────────────
# Marker file (NSSM watchdog trigger)
# ──────────────────────────────────────────────────────────────────────


def _touch_restart_marker(proposal_id: int, proposed_by: str) -> tuple[bool, str]:
    """Vytvori marker file v MARKER_DIR. NSSM watchdog detekuje.

    Filename: <iso_timestamp>_<proposer>_<proposal_id>.touch
    Content: JSON s proposal_id + timestamp pro audit.
    """
    try:
        MARKER_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() else "_" for c in (proposed_by or "unknown"))
        marker_path = MARKER_DIR / f"{ts}_{safe_name}_p{proposal_id}.touch"
        import json
        content = json.dumps({
            "proposal_id": proposal_id,
            "proposed_by": proposed_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False)
        marker_path.write_text(content, encoding="utf-8")
        return True, str(marker_path)
    except Exception as exc:
        logger.exception("_touch_restart_marker failed")
        return False, f"{type(exc).__name__}: {exc}"


def _touch_refresh_secondary_marker(proposal_id: int, deps: bool = False) -> tuple[bool, str]:
    """Marti 10.7.2026: po KAŽDÉM úspěšném deployi automaticky srovnat blue-green
    zálohu (API B) na aktuální A. Zapíše .refreshsec marker → STRATEGIE-RESTART-WATCHER
    spustí refresh_secondary.ps1 (stop B → robocopy A→prev → start B). Dřív se dělalo
    ručně tlačítkem; bez toho hlídač nagoval „⚠ Záloha API B nedohnala A" po každém deployi.
    deps=True (změna pyproject/poetry.lock) → záloha pustí i poetry install.
    Selhání NENÍ fatální — jen warning, deploy A tím není dotčen."""
    try:
        MARKER_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        marker_path = MARKER_DIR / f"{ts}_autodeploy_p{proposal_id}_refreshsec.refreshsec"
        import json
        marker_path.write_text(
            json.dumps({"deps": bool(deps), "by": "auto_deploy", "proposal_id": proposal_id},
                       ensure_ascii=False),
            encoding="utf-8")
        return True, str(marker_path)
    except Exception as exc:
        logger.warning(f"_touch_refresh_secondary_marker failed: {exc}")
        return False, f"{type(exc).__name__}: {exc}"


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────


def propose_deployment(
    description: str,
    conversation_id: int | None = None,
    proposed_by_user_id: int | None = None,
) -> dict:
    """Marti-AI navrhne deployment. Backend zkontroluje git stav, vytvori proposal.

    Vraci:
      ok=True, status='pending', proposal_id, target_sha, files_changed, ...
      ok=False, error pokud git status nesplnen (dirty, no pending, ...)
    """
    if not description or not description.strip():
        return {"ok": False, "error": "Description chybi", "reason": "empty_description"}

    # 1. Git working tree clean check
    clean, detail = _git_working_tree_clean()
    if not clean:
        return {
            "ok": False,
            "error": "Cloud APP working tree neni clean -- manualni intervence vyzadovana.",
            "reason": "dirty_working_tree",
            "git_status": detail[:500],
        }

    # 2. Fetch origin
    fetch_ok, fetch_msg = _git_fetch_origin()
    if not fetch_ok:
        return {
            "ok": False,
            "error": f"git fetch failed: {fetch_msg}",
            "reason": "fetch_failed",
        }

    # 3. Compare HEAD vs origin/main
    head_sha = _git_current_head_sha()
    origin_sha = _git_origin_head_sha()
    if not head_sha or not origin_sha:
        return {
            "ok": False,
            "error": "Nelze ziskat git SHAs (HEAD nebo origin/main).",
            "reason": "git_sha_failed",
        }

    if head_sha == origin_sha:
        return {
            "ok": False,
            "error": "Cloud APP je already up-to-date (HEAD == origin/main).",
            "reason": "already_up_to_date",
            "head_sha": head_sha,
        }

    # 4. Diff stat
    files_count, diff_output = _git_diff_stat(head_sha, origin_sha)
    commit_msg = _git_commit_message_first_line(origin_sha)

    # 5. Insert proposal
    from core.database_data import get_data_session
    from sqlalchemy import text

    session = get_data_session()
    try:
        row = session.execute(
            text(
                "INSERT INTO public.deployment_proposals "
                "(description, commit_sha, commit_message, files_changed, "
                " conversation_id, status, proposed_by_user_id) "
                "VALUES (:desc, :sha, :msg, :fc, :cid, 'pending', :pby) "
                "RETURNING id, proposed_at"
            ),
            {
                "desc": description,
                "sha": origin_sha,
                "msg": commit_msg[:500] if commit_msg else None,
                "fc": files_count,
                "cid": conversation_id,
                "pby": proposed_by_user_id,
            },
        ).first()
        proposal_id = int(row[0])
        session.commit()
    finally:
        session.close()

    # Phase 43 Mini-faze A (19.5.2026): STRATEGIE system_audit bublina v chatu
    try:
        from core.system_actor import system_emit
        if conversation_id is not None:
            system_emit(
                conversation_id=conversation_id,
                content=(
                    f"git fetch OK · target {origin_sha[:7]} '{(commit_msg or '')[:60]}' · "
                    f"{files_count} souborů změněno · proposal #{proposal_id} pending"
                ),
                category="deploy.proposed",
                extra={"proposal_id": proposal_id, "target_sha": origin_sha, "files_changed": files_count},
            )
    except Exception as _e:
        logger.warning(f"propose_deployment system_emit skip: {_e}")

    return {
        "ok": True,
        "status": "pending",
        "proposal_id": proposal_id,
        "target_sha": origin_sha[:12],
        "current_sha": head_sha[:12],
        "files_changed": files_count,
        "commit_message": commit_msg[:200] if commit_msg else "",
        "message_for_chat": (
            f"⚠ Deployment proposal #{proposal_id}: '{description}' "
            f"({files_count} files, target {origin_sha[:7]} '{commit_msg[:80]}'). "
            f"Čeká na approve_deployment({proposal_id}) od Marti / Kristý."
        ),
    }


def _execute_deployment(proposal_id: int) -> dict:
    """Interni: git pull origin main + touch marker. Volano z approve_deployment.

    Returns dict s ok + deploy_output / error.
    """
    from core.database_data import get_data_session
    from sqlalchemy import text

    # Load proposal (vc. conversation_id pro system_emit)
    ds = get_data_session()
    try:
        row = ds.execute(
            text(
                "SELECT id, commit_sha, status, proposed_by_user_id, conversation_id "
                "FROM public.deployment_proposals WHERE id = :id"
            ),
            {"id": proposal_id},
        ).first()
        if not row:
            return {"ok": False, "error": "Proposal not found", "reason": "not_found"}
        target_sha = row[1]
        status = row[2]
        proposer = row[3]
        conv_id = row[4]
        if status not in ("pending", "approved"):
            return {
                "ok": False,
                "error": f"Proposal status={status}, must be pending or approved",
                "reason": "bad_status",
            }
    finally:
        ds.close()

    # Phase 43 Mini-faze A: system_emit helper (used pres celou flow)
    def _emit(content: str, category: str, extra: dict | None = None) -> None:
        if conv_id is None:
            return
        try:
            from core.system_actor import system_emit as _se
            _se(conversation_id=conv_id, content=content, category=category, extra=extra)
        except Exception as _e:
            logger.warning(f"_execute_deployment system_emit skip: {_e}")

    # Mark as 'deploying' + record start time
    ds = get_data_session()
    try:
        ds.execute(
            text(
                "UPDATE public.deployment_proposals "
                "SET status='deploying', deploy_started_at=NOW() WHERE id=:id"
            ),
            {"id": proposal_id},
        )
        ds.commit()
    finally:
        ds.close()

    # Marti 14.6.: HEAD před pull → detekce static-only změn (přeskočit restart).
    _before_sha = _git_current_head_sha()

    # Execute git pull
    pull_ok, pull_output = _git_pull_origin_main()
    if not pull_ok:
        # Mark failed
        ds = get_data_session()
        try:
            ds.execute(
                text(
                    "UPDATE public.deployment_proposals "
                    "SET status='failed', deploy_error=:err, deploy_completed_at=NOW() "
                    "WHERE id=:id"
                ),
                {"id": proposal_id, "err": pull_output[:4000]},
            )
            ds.commit()
        finally:
            ds.close()
        _emit(
            f"git pull SELHAL · proposal #{proposal_id} status='failed' · "
            f"detail: {pull_output[:200]}",
            "deploy.failed",
            {"proposal_id": proposal_id, "error": pull_output[:500]},
        )
        return {"ok": False, "status": "failed", "error": pull_output[:500]}

    # Phase 43: git pull OK -> emit
    _emit(
        f"git pull origin main: {pull_output.strip().split(chr(10))[-1][:120] if pull_output else 'OK'}",
        "deploy.executed",
        {"proposal_id": proposal_id, "target_sha": target_sha[:12] if target_sha else ""},
    )

    # Marti 14.6.: static-only deploy (jen apps/api/static/**, žádné .py) se servíruje
    # z disku → NETŘEBA restart API. Přeskočíme marker → rychlé iterace UI (bez ~5s
    # restartu a odpojení appky). Při .py / jiných změnách restart normálně.
    _after_sha = _git_current_head_sha()
    _changed = _git_changed_files(_before_sha, _after_sha) if (_before_sha and _after_sha) else []
    _static_only = _is_static_only(_changed)

    proposer_label = f"user_{proposer}" if proposer else "unknown"
    if _static_only:
        marker_ok, marker_info = True, "skipped (static-only — bez restartu)"
        _emit(
            "⚡ Static-only deploy — bez restartu API (rychlé). Stačí obnovit stránku.",
            "deploy.executed",
            {"proposal_id": proposal_id, "static_only": True,
             "changed": _changed[:20]},
        )
    else:
        # Touch marker (NSSM watchdog will restart STRATEGIE-API)
        marker_ok, marker_info = _touch_restart_marker(proposal_id, proposer_label)
        if not marker_ok:
            # git pull succeeded but marker failed -- ne fatal, jen warning
            logger.warning(f"deployment #{proposal_id}: marker file failed: {marker_info}")
            _emit(
                f"⚠ marker file failed: {marker_info[:200]} · restart manualne",
                "deploy.failed",
                {"proposal_id": proposal_id, "marker_error": marker_info[:500]},
            )
        else:
            _emit(
                f"marker file touched · STRATEGIE-RESTART-WATCHER detekuje · "
                f"STRATEGIE-API restart pending (~2-5s)",
                "deploy.executed",
                {"proposal_id": proposal_id, "marker_file": marker_info},
            )

    # Mark as deployed (marker triggered restart -- service restart pending)
    ds = get_data_session()
    try:
        ds.execute(
            text(
                "UPDATE public.deployment_proposals SET "
                "  status='deployed', "
                "  deploy_completed_at=NOW(), "
                "  deploy_output=:out, "
                "  restart_marker_file=:mf "
                "WHERE id=:id"
            ),
            {
                "id": proposal_id,
                "out": pull_output[:4000],
                "mf": marker_info if marker_ok else None,
            },
        )
        ds.commit()
    finally:
        ds.close()

    # Auto-srovnání blue-green zálohy B (Marti 10.7.2026): po každém úspěšném deployi
    # povýš zálohu na aktuální kód. Dřív ruční tlačítko → hlídač nagoval po každém deployi.
    # deps podle toho, jestli se měnil pyproject/poetry.lock. Nikdy nefatální.
    try:
        _deps_rs = any(("pyproject" in str(_c).lower() or "poetry.lock" in str(_c).lower())
                       for _c in (_changed or []))
        _rs_ok, _rs_info = _touch_refresh_secondary_marker(proposal_id, _deps_rs)
        _emit(
            ("📦 Auto-srovnání zálohy B naplánováno (RESTART-WATCHER povýší API B)"
             if _rs_ok else f"⚠ Auto-srovnání zálohy B se nepodařilo naplánovat: {_rs_info[:150]}"),
            "deploy.executed",
            {"proposal_id": proposal_id, "refreshsec_marker": (_rs_info if _rs_ok else None),
             "deps": _deps_rs},
        )
    except Exception as _rs_exc:
        logger.warning(f"deployment #{proposal_id}: auto-refresh secondary failed: {_rs_exc}")

    return {
        "ok": True,
        "status": "deployed",
        "proposal_id": proposal_id,
        "target_sha": target_sha[:12] if target_sha else "",
        "marker_file": marker_info if marker_ok else None,
        "pull_output_excerpt": pull_output[:300],
    }


def approve_deployment(proposal_id: int, decided_by_user_id: int, reason: str | None = None) -> dict:
    """Marti / Kristy approve -> _execute_deployment.

    Authority: is_marti_parent=True only.
    """
    from core.database_core import get_core_session
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_core import User
    from sqlalchemy import text

    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=decided_by_user_id).first()
        if not user:
            return {"ok": False, "error": "Unknown user", "reason": "no_user"}
        if not bool(getattr(user, "is_marti_parent", False)):
            return {
                "ok": False,
                "error": "Pouze rodice (is_marti_parent=True) mohou approve deployments.",
                "reason": "not_parent",
            }
    finally:
        cs.close()

    # Update proposal -> approved (intermediate state pred deploy)
    ds = get_data_session()
    try:
        row = ds.execute(
            text(
                "UPDATE public.deployment_proposals SET "
                "  status='approved', "
                "  decided_by_user_id=:dby, "
                "  decided_at=NOW(), "
                "  decision_reason=:reason "
                "WHERE id=:id AND status='pending' "
                "RETURNING id"
            ),
            {"id": proposal_id, "dby": decided_by_user_id, "reason": reason},
        ).first()
        if not row:
            return {
                "ok": False,
                "error": f"Proposal #{proposal_id} nenalezen nebo neni pending.",
                "reason": "not_pending",
            }
        ds.commit()
    finally:
        ds.close()

    # Execute git pull + touch marker (synchronous; restart je async via watchdog)
    exec_result = _execute_deployment(proposal_id)
    return exec_result


def reject_deployment(proposal_id: int, decided_by_user_id: int, reason: str | None = None) -> dict:
    """Marti / Kristy reject -> close as rejected."""
    from core.database_core import get_core_session
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_core import User
    from sqlalchemy import text

    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=decided_by_user_id).first()
        if not user:
            return {"ok": False, "error": "Unknown user", "reason": "no_user"}
        if not bool(getattr(user, "is_marti_parent", False)):
            return {
                "ok": False,
                "error": "Pouze rodice (is_marti_parent=True) mohou rozhodovat deployments.",
                "reason": "not_parent",
            }
    finally:
        cs.close()

    ds = get_data_session()
    conv_id_for_emit: int | None = None
    try:
        row = ds.execute(
            text(
                "UPDATE public.deployment_proposals SET "
                "  status='rejected', "
                "  decided_by_user_id=:dby, "
                "  decided_at=NOW(), "
                "  decision_reason=:reason "
                "WHERE id=:id AND status='pending' "
                "RETURNING id, conversation_id"
            ),
            {"id": proposal_id, "dby": decided_by_user_id, "reason": reason},
        ).first()
        if not row:
            return {
                "ok": False,
                "error": f"Proposal #{proposal_id} nenalezen nebo neni pending.",
                "reason": "not_pending",
            }
        conv_id_for_emit = row[1]
        ds.commit()
    finally:
        ds.close()

    # Phase 43 Mini-faze A: STRATEGIE system_audit bublina v chatu
    try:
        if conv_id_for_emit is not None:
            from core.system_actor import system_emit
            system_emit(
                conversation_id=conv_id_for_emit,
                content=(
                    f"Proposal #{proposal_id} rejected" + (f" · reason: {reason}" if reason else "")
                ),
                category="deploy.rejected",
                extra={"proposal_id": proposal_id, "decided_by_user_id": decided_by_user_id, "reason": reason},
            )
    except Exception as _e:
        logger.warning(f"reject_deployment system_emit skip: {_e}")

    return {"ok": True, "status": "rejected", "proposal_id": proposal_id, "reason": reason or ""}
