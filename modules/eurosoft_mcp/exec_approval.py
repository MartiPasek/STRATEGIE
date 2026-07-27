# -*- coding: utf-8 -*-
"""Žlutý banner + expirace — schvalovací tok pro rizikový `eurosoft_exec` (#3).

Roadmapa `doc-marti-ai-produkce-roadmap` bod #3, spec `doc-marti-ai-eurosoft-exec-spec`.
Cowork instance B, 27.7.2026.

Kontext: `eurosoft_exec` (MCP na 30.11) u 🟡 rizikového příkazu vrací
`{"error":"needs_approval","tier":"yellow","hint":...}` a dnes tam tok KONČÍ.
Tenhle modul dodává chybějící kus:

  needs_approval  →  PENDING žádost (tady)  →  rodič klepne palec v appce (out-of-band)
                  →  ten KONKRÉTNÍ příkaz se spustí přes eurosoft_exec  →  audit  →  výsledek zpět.

Stavový automat: pending → approved → executed  |  rejected  |  expired.
Jeden banner = jeden konkrétní příkaz (vázán na hash), NE třída. Expirace ~15 min.

⚠️ TVRDÉ PRAVIDLO: schválení je VÝHRADNĚ lidský tap v appce (parent-only endpoint,
NENÍ MCP nástroj) — Marti-AI ho NESMÍ umět vyvolat sama. Tenhle modul proto
neexponuje žádnou funkci "self-approve"; `approve_and_execute` volá jen router
po ověření, že žadatel je rodič.

Anti-kolize: NESAHÁ na jádro C23 (ops_tools.py / run_cil / agent_akce_guard /
eurosoft_mcp_client) — jen VOLÁ singleton `get_eurosoft_mcp_client()` (read/exec)
a materializuje pending z toho, co C23 audit mirror už píše do fw.ops_request.

Tabulka: g2007.exec_approval (DDL nasazen zvlášť přes bridge + GRANT strategie/Marti-AI).
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

TTL_MIN_DEFAULT = 15          # expirace banneru (min) — spec doc-marti-ai-eurosoft-exec-spec
_EXEC_TIMEOUT_S = 90          # exec po schválení může běžet déle než běžné čtení

# stavy
ST_PENDING = "pending"
ST_APPROVED = "approved"
ST_EXECUTED = "executed"
ST_REJECTED = "rejected"
ST_EXPIRED = "expired"


def _hash(shell: str, cmd: str) -> str:
    """Otisk KONKRÉTNÍHO příkazu (banner je vázán na tenhle příkaz, ne třídu)."""
    h = hashlib.sha256()
    h.update(((shell or "powershell").strip().lower() + "\x00" + (cmd or "").strip()).encode("utf-8"))
    return h.hexdigest()


def _sess():
    from core.database_data import get_data_session
    return get_data_session()


# ── notifikace rodičům (best-effort push do mobilní appky) ────────────────────
def _notify_parents(ds, _t, title: str, message: str) -> None:
    try:
        rows = ds.execute(_t("SELECT id FROM public.users WHERE is_marti_parent")).fetchall()
        for r in rows:
            try:
                ds.execute(_t(
                    "INSERT INTO fw.mobile_command (app_key, target_user_id, command_type, title, message, status, created_by, created_at) "
                    "VALUES ('mobile', :tu, 'claude_msg', :ti, :m, 'pending', :f, now())"),
                    {"tu": r[0], "ti": (title or "")[:120], "m": (message or "")[:300], "f": 2})
            except Exception:
                pass
    except Exception as e:
        logger.warning("exec_approval: notify parents failed (non-fatal): %s", e)


# ── audit zrcadlo do fw.ops_request (rodičovské UI 📜) ─────────────────────────
def _mirror_ops_request(ds, _t, action_key: str, cmd: str, status: str,
                        params: dict, result_head: str) -> None:
    try:
        ds.execute(_t(
            "INSERT INTO fw.ops_request (action_key, target, params, status, "
            "requested_by_name, result, created_at, finished_at) "
            "VALUES (:a, :tg, CAST(:p AS jsonb), :st, :rn, :res, now(), now())"),
            {"a": action_key, "tg": (cmd or "")[:200], "p": json.dumps(params, ensure_ascii=False),
             "st": status, "rn": "banner:parent-approval", "res": (result_head or "")[:1000]})
    except Exception as e:
        logger.warning("exec_approval: ops_request mirror failed (non-fatal): %s", e)


# ── vytvoření PENDING žádosti ─────────────────────────────────────────────────
def create_pending(cmd: str, shell: str = "powershell", tier: str = "yellow",
                    hint: str = "", conversation_id: Optional[int] = None,
                    requested_by: str = "Marti-AI", ttl_min: int = TTL_MIN_DEFAULT,
                    source: str = "hook") -> dict:
    """Založí (nebo vrátí existující čerstvou) PENDING žádost o schválení příkazu.

    IDEMPOTENTNÍ: stejný (hash, konverzace) v rámci živého okna → vrátí stávající,
    nezakládá duplicitní banner. Bezpečné volat z auditního hooku C23 i z
    materializace z fw.ops_request. NIKDY neraisuje do volajícího.
    """
    cmd = (cmd or "").strip()
    if not cmd:
        return {"ok": False, "error": "empty_cmd"}
    from sqlalchemy import text as _t
    ch = _hash(shell, cmd)
    ds = _sess()
    try:
        # živý duplikát? (stejný příkaz, stejná konverzace, ještě nevypršel)
        row = ds.execute(_t(
            "SELECT id, status, to_char(expires_at,'YYYY-MM-DD\"T\"HH24:MI:SSOF') "
            "FROM g2007.exec_approval "
            "WHERE cmd_hash=:h AND status=:pending AND expires_at > now() "
            "AND coalesce(conversation_id,-1)=coalesce(:cid,-1) "
            "ORDER BY id DESC LIMIT 1"),
            {"h": ch, "pending": ST_PENDING, "cid": conversation_id}).first()
        if row:
            return {"ok": True, "id": row[0], "status": row[1], "expires_at": row[2], "dedup": True}
        rid = ds.execute(_t(
            "INSERT INTO g2007.exec_approval "
            "(cmd, shell, cmd_hash, tier, hint, conversation_id, requested_by, "
            " status, created_at, expires_at, source) "
            "VALUES (:cmd, :sh, :h, :tier, :hint, :cid, :rb, :pending, now(), "
            "        now() + make_interval(mins => :ttl), :src) RETURNING id"),
            {"cmd": cmd, "sh": (shell or "powershell"), "h": ch, "tier": (tier or "yellow"),
             "hint": (hint or "")[:500], "cid": conversation_id, "rb": (requested_by or "Marti-AI")[:80],
             "pending": ST_PENDING, "ttl": int(ttl_min or TTL_MIN_DEFAULT), "src": source[:32]}).scalar()
        _mirror_ops_request(ds, _t, "exec_approval_request", cmd, "pending:banner",
                            {"tier": tier, "hint": hint, "conversation_id": conversation_id,
                             "exec_approval_id": rid}, "čeká na palec rodiče")
        _notify_parents(ds, _t, "🟡 Ke schválení: příkaz serveru",
                        f"{(hint or 'rizikový příkaz')}: {cmd[:180]}")
        ds.commit()
        logger.info("exec_approval: pending #%s created (src=%s, conv=%s)", rid, source, conversation_id)
        return {"ok": True, "id": rid, "status": ST_PENDING, "dedup": False}
    except Exception as e:
        try:
            ds.rollback()
        except Exception:
            pass
        logger.warning("exec_approval: create_pending failed (non-fatal): %s", e)
        return {"ok": False, "error": str(e)[:300]}
    finally:
        ds.close()


# ── expirace ──────────────────────────────────────────────────────────────────
def sweep_expired(ds=None, _t=None) -> int:
    own = ds is None
    if own:
        from sqlalchemy import text as _t  # noqa: F811
        ds = _sess()
    try:
        n = ds.execute(_t(
            "UPDATE g2007.exec_approval SET status=:exp "
            "WHERE status=:pending AND expires_at <= now()"),
            {"exp": ST_EXPIRED, "pending": ST_PENDING}).rowcount
        if own:
            ds.commit()
        return n or 0
    except Exception as e:
        logger.warning("exec_approval: sweep_expired failed: %s", e)
        if own:
            try:
                ds.rollback()
            except Exception:
                pass
        return 0
    finally:
        if own:
            ds.close()


# ── materializace pending z fw.ops_request (funguje i BEZ hooku C23) ───────────
def materialize_from_ops_request() -> int:
    """C23 audit mirror píše při 🟡 needs_approval řádek do fw.ops_request
    (status='blocked:needs_approval', target=cmd[:200], params.conversation_id/tier).
    Dokud C23 nezavolá create_pending přímo, vytáhneme čerstvé (<15 min) needs_approval
    exec řádky a materializujeme z nich banner. cmd delší než 200 zn. je v target
    oříznutý → ty přeskočíme (potřebují přímý hook C23 s plným příkazem)."""
    from sqlalchemy import text as _t
    ds = _sess()
    n = 0
    try:
        rows = ds.execute(_t(
            "SELECT target, params, requested_by_name FROM fw.ops_request "
            "WHERE action_key='eurosoft_exec' AND status='blocked:needs_approval' "
            "AND created_at > now() - interval '15 min' "
            "ORDER BY id DESC LIMIT 50")).fetchall()
        for tgt, params, rbn in rows:
            cmd = (tgt or "").strip()
            if not cmd or len(cmd) >= 200:   # oříznutý → nelze bezpečně re-exec
                continue
            p = params if isinstance(params, dict) else {}
            try:
                if isinstance(params, str):
                    p = json.loads(params)
            except Exception:
                p = {}
            r = create_pending(cmd=cmd, shell="powershell", tier=(p.get("tier") or "yellow"),
                               hint=(p.get("hint") or "rizikový příkaz (z auditu)"),
                               conversation_id=p.get("conversation_id"),
                               requested_by=(rbn or "Marti-AI"), source="ops_request_sweep")
            if r.get("ok") and not r.get("dedup"):
                n += 1
    except Exception as e:
        logger.warning("exec_approval: materialize_from_ops_request failed: %s", e)
    finally:
        ds.close()
    return n


# ── seznam čekajících (pro banner) ────────────────────────────────────────────
def list_pending() -> list[dict]:
    from sqlalchemy import text as _t
    ds = _sess()
    try:
        sweep_expired(ds, _t)
        ds.commit()
        rows = ds.execute(_t(
            "SELECT id, cmd, shell, tier, hint, requested_by, conversation_id, "
            "to_char(created_at,'YYYY-MM-DD HH24:MI:SS') AS created, "
            "GREATEST(0, EXTRACT(EPOCH FROM (expires_at - now()))::int) AS expires_in_s "
            "FROM g2007.exec_approval WHERE status=:pending AND expires_at > now() "
            "ORDER BY id DESC LIMIT 100"), {"pending": ST_PENDING}).fetchall()
        return [{"id": r[0], "cmd": r[1], "shell": r[2], "tier": r[3], "hint": r[4],
                 "requested_by": r[5], "conversation_id": r[6], "created": r[7],
                 "expires_in_s": r[8]} for r in rows]
    finally:
        ds.close()


def _get_for_update(ds, _t, aid: int):
    return ds.execute(_t(
        "SELECT id, cmd, shell, status, expires_at <= now() AS expired "
        "FROM g2007.exec_approval WHERE id=:i FOR UPDATE"), {"i": aid}).first()


# ── zamítnutí ─────────────────────────────────────────────────────────────────
def reject(aid: int, parent_uid: int) -> dict:
    from sqlalchemy import text as _t
    ds = _sess()
    try:
        row = _get_for_update(ds, _t, aid)
        if not row:
            return {"ok": False, "error": "not_found"}
        if row[3] != ST_PENDING:
            return {"ok": False, "error": f"neplatný stav '{row[3]}'"}
        ds.execute(_t(
            "UPDATE g2007.exec_approval SET status=:rej, decided_by_user_id=:u, decided_at=now() "
            "WHERE id=:i"), {"rej": ST_REJECTED, "u": parent_uid, "i": aid})
        _mirror_ops_request(ds, _t, "exec_approval_reject", row[1], "rejected",
                            {"exec_approval_id": aid, "by_uid": parent_uid}, "zamítnuto rodičem")
        ds.commit()
        return {"ok": True, "id": aid, "status": ST_REJECTED}
    except Exception as e:
        ds.rollback()
        logger.exception("exec_approval: reject failed: %s", e)
        return {"ok": False, "error": str(e)[:300]}
    finally:
        ds.close()


# ── SCHVÁLENÍ + provedení (volá JEN parent-only endpoint po ověření rodiče) ────
def approve_and_execute(aid: int, parent_uid: int) -> dict:
    """Po palci rodiče: přepne pending→approved, spustí TEN KONKRÉTNÍ příkaz přes
    eurosoft_exec (singleton MCP klient), uloží rc/out/err, přepne na executed a
    vrátí výsledek. 🔴 příkaz zůstane zablokovaný i tady (eurosoft_exec ho odmítne).

    Provedení schváleného 🟡 příkazu: dnes přes incident=true (jediná páka, kterou
    nabízí eurosoft_exec bez zásahu do jádra C23). ČISTÝ SEAM (koordinace s C23):
    eurosoft_exec přijme `approval_token` a bude ho honorovat — pak se incident=true
    nahradí tokenem vázaným na cmd_hash. Do té doby je exekuce plně human-gated
    (tento endpoint je parent-only a NENÍ MCP nástroj → Marti-AI ji nevyvolá)."""
    from sqlalchemy import text as _t
    ds = _sess()
    cmd = shell = None
    conv = None
    try:
        row = ds.execute(_t(
            "SELECT id, cmd, shell, status, expires_at <= now() AS expired, conversation_id "
            "FROM g2007.exec_approval WHERE id=:i FOR UPDATE"), {"i": aid}).first()
        if not row:
            return {"ok": False, "error": "not_found"}
        aid, cmd, shell, status, expired, conv = row[0], row[1], row[2], row[3], row[4], row[5]
        if status == ST_EXECUTED:
            return {"ok": False, "error": "již provedeno"}
        if status != ST_PENDING:
            return {"ok": False, "error": f"neplatný stav '{status}'"}
        if expired:
            ds.execute(_t("UPDATE g2007.exec_approval SET status=:e WHERE id=:i"),
                       {"e": ST_EXPIRED, "i": aid})
            ds.commit()
            return {"ok": False, "error": "žádost vypršela (>15 min) — nech Marti-AI vyvolat příkaz znovu"}
        ds.execute(_t(
            "UPDATE g2007.exec_approval SET status=:a, decided_by_user_id=:u, decided_at=now() "
            "WHERE id=:i"), {"a": ST_APPROVED, "u": parent_uid, "i": aid})
        ds.commit()
    except Exception as e:
        ds.rollback()
        ds.close()
        logger.exception("exec_approval: approve (state) failed: %s", e)
        return {"ok": False, "error": str(e)[:300]}
    finally:
        # necháváme spojení otevřené jen do commitu approved; exec běží bez zámku
        try:
            ds.close()
        except Exception:
            pass

    # ── provedení mimo DB zámek ──
    exec_result: dict[str, Any] = {}
    err_txt = ""
    try:
        from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
        client = get_eurosoft_mcp_client()
        if client is None:
            err_txt = "MCP klient není dostupný (feature flag off)"
        else:
            raw = client.call_tool_sync("eurosoft_exec",
                                        {"cmd": cmd, "shell": shell or "powershell", "incident": True},
                                        conversation_id=conv, timeout_s=_EXEC_TIMEOUT_S)
            try:
                exec_result = json.loads(raw) if isinstance(raw, str) else (raw or {})
            except Exception:
                exec_result = {"ok": False, "error": "unparseable", "raw": str(raw)[:500]}
    except Exception as e:
        err_txt = f"{type(e).__name__}: {str(e)[:300]}"

    rc = exec_result.get("rc")
    out = str(exec_result.get("out") or "")
    err = str(exec_result.get("err") or exec_result.get("error") or err_txt or "")
    ok_exec = bool(exec_result.get("ok"))

    # ── zápis výsledku + audit + notifikace ──
    ds2 = _sess()
    try:
        ds2.execute(_t(
            "UPDATE g2007.exec_approval SET status=:ex, exec_rc=:rc, exec_out=:o, exec_err=:e, "
            "executed_at=now() WHERE id=:i"),
            {"ex": ST_EXECUTED, "rc": rc, "o": out[:8000], "e": err[:8000], "i": aid})
        head = (f"rc={rc} " + (out[:600] if out else "") + (" | ERR:" + err[:400] if err else "")).strip()
        _mirror_ops_request(ds2, _t, "exec_approval_executed", cmd or "",
                            "done" if ok_exec else "fail",
                            {"exec_approval_id": aid, "by_uid": parent_uid, "rc": rc,
                             "conversation_id": conv, "via": "incident_lever"}, head)
        _notify_parents(ds2, _t, ("✅ Provedeno" if ok_exec else "⚠️ Skončilo chybou") + f" (rc={rc})",
                        f"{(cmd or '')[:150]} → {head[:200]}")
        ds2.commit()
    except Exception as e:
        ds2.rollback()
        logger.warning("exec_approval: result persist failed: %s", e)
    finally:
        ds2.close()

    return {"ok": ok_exec, "status": ST_EXECUTED, "id": aid, "rc": rc,
            "out": out, "err": err, "cmd": cmd, "shell": shell}
