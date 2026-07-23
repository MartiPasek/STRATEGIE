# -*- coding: utf-8 -*-
"""handlers — napojení Tool Factory na živou app (dispatch meta-nástrojů + běh
generovaných nástrojů + zápisy do g2007). VŠE za vypínačem TOOLFACTORY_ENABLED
a v try/except — když je vypnuto nebo cokoli selže, vrací None a normální nástroje
běží dál nedotčeně.

Governance: autorství+test autonomně (Marti-AI), aktivace jen lidský rodič.
DB: g2007 zápisy přes core.database.get_session() (role Marti-AI/owner) — stejně
jako @@GODOC. Parent check přes core.database_core.get_core_session().
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

MARTI_AI_ENTITA_ID = 2

# ── Vypínač ─────────────────────────────────────────────────────────────────────
# Řízeno klíčem g2007.nastaveni('toolfactory_enabled') = 'on'|'off' — Marti ho
# přepíná přes most (banner), stejně jako composer_mode. Env TOOLFACTORY_ENABLED=1
# je jen test-override. Krátká cache, ať se nečte DB při každé zprávě.
_flag_cache = {"val": False, "ts": 0.0}
_FLAG_TTL = 15.0


def _enabled() -> bool:
    if os.environ.get("TOOLFACTORY_ENABLED") == "1":
        return True
    now = time.monotonic()
    if now - _flag_cache["ts"] < _FLAG_TTL:
        return _flag_cache["val"]
    val = False
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            h = sg.execute(_t("SELECT hodnota FROM g2007.nastaveni WHERE klic='toolfactory_enabled'")).scalar()
            val = str(h).strip().lower() == "on"
        finally:
            sg.close()
    except Exception:
        val = False
    _flag_cache["val"] = val
    _flag_cache["ts"] = now
    return val


# ── Meta-nástroje (v1, jednokrokové — jednodušší tok pro LLM) ────────────────────
V1_META_SPECS = [
    {
        "name": "create_tool",
        "description": (
            "🛠️ SEBEROZVOJ: navrhni SVŮJ NOVÝ nástroj. Zadej kod (^[a-z][a-z0-9_]+$), "
            "nazev, popis, parametry (JSON schema vstupu) a kod_python = TĚLO funkce "
            "run(args, ctx). K dispozici máš: need(args,'x') (povinný argument), ok(text) "
            "(návratová hodnota) a pro ČTENÍ Z DATABÁZE ctx.fetch('SELECT ... WHERE x=:x', "
            "{'x': hodnota}) → vrací list dictů (parametry přes :bind, NE string concat). "
            "Užitečné tabulky (data DB): conversations(audit_status['pending'|'audited'|"
            "'excluded'], audited_at, last_message_at, tenant_id, title), messages, memories. "
            "Nástroj se hned otestuje v sandboxu nad test_cases; když projde, podá se rodiči "
            "ke schválení (sama ho neaktivuješ). Po schválení ho budeš moct rovnou používat."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "kod": {"type": "string"},
                "nazev": {"type": "string"},
                "popis": {"type": "string"},
                "parametry": {"type": "object", "description": "input_schema nového nástroje."},
                "kod_python": {"type": "string", "description": "Tělo run(args, ctx) — vrací string přes ok(...)."},
                "test_cases": {
                    "type": "array",
                    "description": "Testy: [{args:{...}, expect?:'podřetězec výstupu'}]. Aspoň 1.",
                    "items": {"type": "object"},
                },
            },
            "required": ["kod", "nazev", "popis", "parametry", "kod_python", "test_cases"],
        },
    },
    {
        "name": "approve_tool",
        "description": (
            "Rodič SCHVÁLÍ návrh nástroje → aktivace, nástroj se stane použitelným. "
            "JEN LIDSKÝ RODIČ (Marti/Kristý). Ty sama vlastní nástroj neschválíš."
        ),
        "input_schema": {"type": "object", "properties": {
            "proposal_id": {"type": "integer"}, "reason": {"type": "string"}},
            "required": ["proposal_id"]},
    },
    {
        "name": "reject_tool",
        "description": "Rodič ZAMÍTNE návrh nástroje. Jen lidský rodič.",
        "input_schema": {"type": "object", "properties": {
            "proposal_id": {"type": "integer"}, "reason": {"type": "string"}},
            "required": ["proposal_id", "reason"]},
    },
    {
        "name": "list_tool_proposals",
        "description": "Vypiš čekající návrhy nástrojů (pending) + aktivní generované nástroje.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "disable_tool",
        "description": "Kill switch: rodič odpojí aktivní generovaný nástroj (kod). Jen rodič.",
        "input_schema": {"type": "object", "properties": {
            "kod": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["kod", "reason"]},
    },
]
META_NAMES = frozenset(s["name"] for s in V1_META_SPECS)

# ── Fáze 0: Marti-AI spustí VLASTNÍ agentí smyčku (read-only) ────────────────────
RUN_AS_AGENT_SPEC = {
    "name": "run_as_agent",
    "description": (
        "🧠 AGENT (seberozvoj, Fáze 0): proběhni zadaný CÍL svojí VLASTNÍ agentí "
        "smyčkou — autonomně, mnoha tahy, čteš repo přes Read/Grep/Glob a vrátíš "
        "výsledek. Zatím JEN ČTENÍ (analýzy, průzkum repa, návrhy) — bez zápisu. "
        "Toto NENÍ delegace na Claude-23: běžíš TY, pod svojí identitou. "
        "Zadej 'goal' = co mám samostatně zjistit / vyrobit."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"goal": {"type": "string", "description": "Cíl k autonomnímu proběhnutí (read-only)."}},
        "required": ["goal"],
    },
}

# ── Cache aktivních generovaných speců (invalidace při změně) ────────────────────
_spec_cache: Optional[list] = None


def _bump_cache():
    global _spec_cache
    _spec_cache = None


def _is_parent(user_id: Optional[int]) -> bool:
    if not user_id:
        return False
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        return bool(u and getattr(u, "is_marti_parent", False))
    finally:
        cs.close()


def _agent_allowed(user_id: Optional[int]) -> bool:
    # run_as_agent (Faze 0): jen admin NEBO rodic, a jen kdyz ma zapnuty
    # per-user prepinac users.agent_enabled (PATCH /me/agent-enabled).
    if not user_id:
        return False
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if not u:
            return False
        is_ap = bool(getattr(u, "is_admin", False) or getattr(u, "is_marti_parent", False))
        return bool(is_ap and getattr(u, "agent_enabled", False))
    finally:
        cs.close()


def _audit(sg, akce, user_id=None, nastroj_id=None, proposal_id=None, detail=None):
    from sqlalchemy import text as _t
    sg.execute(_t(
        "INSERT INTO g2007.tool_audit (actor_user_id, actor_entita_id, akce, nastroj_id, proposal_id, detail) "
        "VALUES (:u, :e, :a, :n, :p, CAST(:d AS jsonb))"),
        {"u": user_id, "e": MARTI_AI_ENTITA_ID, "a": akce, "n": nastroj_id, "p": proposal_id,
         "d": json.dumps(detail or {}, ensure_ascii=False)})


def _active_generated_rows(sg):
    from sqlalchemy import text as _t
    return sg.execute(_t(
        "SELECT id, kod, nazev, popis_plny, parametry, selftest_verdikt FROM g2007.nastroj "
        "WHERE implementace LIKE 'generated:%' AND stav_zivota='active' ORDER BY kod")).mappings().all()


def _ensure_generated_file(kod, spec, code_body):
    """Regeneruj generated/<kod>.py z DB, pokud soubor chybí (odolnost vůči redeployi)."""
    from tool_registry import GENERATED_DIR
    from tool_registry import runtime as RT
    path = os.path.join(GENERATED_DIR, f"{kod}.py")
    if not os.path.exists(path):
        RT.write_generated(kod, spec, code_body)
    return path


# ── Veřejné API pro živou app ────────────────────────────────────────────────────
def effective_factory_specs(is_default_persona: bool) -> list:
    """Specy, které se přidají do živého seznamu nástrojů Marti-AI (jen default persona)."""
    if not _enabled() or not is_default_persona:
        return []
    global _spec_cache
    if _spec_cache is not None:
        return _spec_cache
    specs = list(V1_META_SPECS)
    specs.append(RUN_AS_AGENT_SPEC)  # Fáze 0 — vlastní agentí smyčka (handler gate-uje flag)
    try:
        from core.database import get_session
        sg = get_session()
        try:
            for r in _active_generated_rows(sg):
                sv = r["selftest_verdikt"] or {}
                spec = (sv or {}).get("spec") if isinstance(sv, dict) else None
                if spec:
                    specs.append({k: v for k, v in spec.items() if not str(k).startswith("_")})
        finally:
            sg.close()
    except Exception as e:
        logger.exception(f"TOOLFACTORY | effective specs: {e}")
    _spec_cache = specs
    return specs


def handle(tool_name: str, tool_input: dict, user_id: Optional[int],
           conversation_id: Optional[int]) -> Optional[str]:
    """Vrátí string, pokud jde o Tool Factory (meta nebo generovaný nástroj); jinak None."""
    if not _enabled():
        return None
    try:
        if tool_name == "create_tool":
            return _create(tool_input, user_id)
        if tool_name == "approve_tool":
            return _approve(tool_input, user_id)
        if tool_name == "reject_tool":
            return _reject(tool_input, user_id)
        if tool_name == "list_tool_proposals":
            return _list()
        if tool_name == "disable_tool":
            return _disable(tool_input, user_id)
        if tool_name == "run_as_agent":
            return _run_as_agent(tool_input, user_id, conversation_id)
        if tool_name in META_NAMES:
            return None
        # generovaný nástroj?
        return _dispatch_generated(tool_name, tool_input, user_id, conversation_id)
    except Exception as e:
        logger.exception(f"TOOLFACTORY | handle {tool_name}: {e}")
        return f"❌ Tool Factory chyba u '{tool_name}': {type(e).__name__}: {e}"


# ── Jednotlivé handlery ──────────────────────────────────────────────────────────
def _create(inp: dict, user_id) -> str:
    from tool_registry import runtime as RT
    from tool_registry.factory import validate_kod
    from core.database import get_session
    from sqlalchemy import text as _t

    kod = (inp.get("kod") or "").strip()
    validate_kod(kod)
    nazev = (inp.get("nazev") or "").strip() or kod
    popis = (inp.get("popis") or "").strip()
    parametry = inp.get("parametry") or {"type": "object", "properties": {}}
    code_body = inp.get("kod_python") or ""
    test_cases = inp.get("test_cases") or []
    spec = {"name": kod, "description": popis, "input_schema": parametry}

    # self-test dostane DB přístup (ctx.fetch → data DB), ať se otestuje i nástroj co čte data
    from tool_registry._common import ToolContext as _TC
    from core.database_data import get_data_session as _gds_test
    res = RT.selftest(kod, spec, code_body, test_cases,
                      ctx=_TC(entita_id=MARTI_AI_ENTITA_ID, db_session_factory=_gds_test))
    if not res.ok:
        return (f"❌ Self-test nástroje '{kod}' NEPROŠEL — nic jsem neuložila.\n"
                f"{json.dumps(res.to_dict(), ensure_ascii=False)[:600]}")

    sg = get_session()
    try:
        exists = sg.execute(_t("SELECT count(*) FROM g2007.nastroj WHERE kod=:k"), {"k": kod}).scalar()
        if exists:
            return f"❌ Nástroj s kódem '{kod}' už existuje — zvol jiný kod nebo použij revizi."
        payload = {"spec": spec, "code": code_body, "verdict": res.to_dict()}
        nid = sg.execute(_t(
            "INSERT INTO g2007.nastroj (kod, nazev, kategorie, implementace, popis, popis_plny, "
            "parametry, stav, stav_zivota, autor_entita_id, verze, selftest_verdikt) "
            "VALUES (:k,:nz,'generated',:impl,:po,:po, CAST(:pm AS jsonb),'navrh','ceka_na_schvaleni', "
            ":ae,1, CAST(:sv AS jsonb)) RETURNING id"),
            {"k": kod, "nz": nazev, "impl": "generated:" + kod, "po": popis,
             "pm": json.dumps(parametry, ensure_ascii=False), "ae": MARTI_AI_ENTITA_ID,
             "sv": json.dumps(payload, ensure_ascii=False)}).scalar()
        pid = sg.execute(_t(
            "INSERT INTO g2007.tool_proposal (nastroj_id, autor_entita_id, description, selftest, status) "
            "VALUES (:n,:ae,:d, CAST(:s AS jsonb),'pending') RETURNING id"),
            {"n": nid, "ae": MARTI_AI_ENTITA_ID, "d": f"Nový nástroj '{kod}': {popis}"[:500],
             "s": json.dumps(payload, ensure_ascii=False)}).scalar()
        _audit(sg, "propose", user_id=user_id, nastroj_id=nid, proposal_id=pid,
               detail={"kod": kod, "selftest_ok": True})
        sg.commit()
    finally:
        sg.close()
    return (f"✅ Nástroj '{kod}' prošel self-testem ({len(res.cases)} případů) a **návrh #{pid} čeká na "
            f"schválení rodiče**. Až ho Marti/Kristý schválí (approve_tool), budu ho moct používat.")


def _approve(inp: dict, user_id) -> str:
    from tool_registry.factory import can_approve
    from core.database import get_session
    from sqlalchemy import text as _t

    pid = inp.get("proposal_id")
    if not _is_parent(user_id):
        return "🚫 Schválit nástroj může jen rodič (Marti nebo Kristýna)."
    ok_appr, why = can_approve(user_id, MARTI_AI_ENTITA_ID, lambda u: u == user_id)  # už víme, že je rodič
    if not ok_appr:
        return f"🚫 {why}"
    sg = get_session()
    try:
        row = sg.execute(_t(
            "SELECT p.id, p.nastroj_id, p.status, p.selftest, n.kod FROM g2007.tool_proposal p "
            "JOIN g2007.nastroj n ON n.id=p.nastroj_id WHERE p.id=:p"), {"p": pid}).mappings().first()
        if not row:
            return f"❌ Návrh #{pid} neexistuje."
        if row["status"] != "pending":
            return f"❌ Návrh #{pid} už není 'pending' (stav {row['status']})."
        payload = row["selftest"] or {}
        spec = payload.get("spec"); code = payload.get("code")
        if not spec or code is None:
            return f"❌ Návrh #{pid} nemá uložený kód/spec."
        _ensure_generated_file(row["kod"], spec, code)
        sg.execute(_t("UPDATE g2007.nastroj SET stav_zivota='active', updated_at=now() WHERE id=:n"),
                   {"n": row["nastroj_id"]})
        sg.execute(_t("UPDATE g2007.tool_proposal SET status='approved', approved_by=:u, "
                      "reason=:r, decided_at=now() WHERE id=:p"),
                   {"u": user_id, "r": inp.get("reason"), "p": pid})
        _audit(sg, "approve", user_id=user_id, nastroj_id=row["nastroj_id"], proposal_id=pid,
               detail={"kod": row["kod"]})
        sg.commit()
    finally:
        sg.close()
    _bump_cache()
    return f"✅ Nástroj '{row['kod']}' schválen a **aktivován** — od teď ho můžu používat."


def _reject(inp: dict, user_id) -> str:
    from core.database import get_session
    from sqlalchemy import text as _t
    pid = inp.get("proposal_id")
    if not _is_parent(user_id):
        return "🚫 Zamítnout návrh může jen rodič."
    sg = get_session()
    try:
        row = sg.execute(_t("SELECT nastroj_id, status FROM g2007.tool_proposal WHERE id=:p"),
                         {"p": pid}).mappings().first()
        if not row or row["status"] != "pending":
            return f"❌ Návrh #{pid} není čekající."
        sg.execute(_t("UPDATE g2007.tool_proposal SET status='rejected', approved_by=:u, reason=:r, "
                      "decided_at=now() WHERE id=:p"), {"u": user_id, "r": inp.get("reason"), "p": pid})
        sg.execute(_t("UPDATE g2007.nastroj SET stav_zivota='zamitnuty', updated_at=now() WHERE id=:n"),
                   {"n": row["nastroj_id"]})
        _audit(sg, "reject", user_id=user_id, nastroj_id=row["nastroj_id"], proposal_id=pid,
               detail={"reason": inp.get("reason")})
        sg.commit()
    finally:
        sg.close()
    _bump_cache()
    return f"Návrh #{pid} zamítnut."


def _list() -> str:
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        pend = sg.execute(_t(
            "SELECT p.id, n.kod, p.description FROM g2007.tool_proposal p "
            "JOIN g2007.nastroj n ON n.id=p.nastroj_id WHERE p.status='pending' ORDER BY p.id")).mappings().all()
        act = [r["kod"] for r in _active_generated_rows(sg)]
    finally:
        sg.close()
    lines = ["📋 **Čekající návrhy nástrojů:**"]
    lines += ([f"  • #{r['id']} {r['kod']} — {r['description']}" for r in pend] or ["  (žádné)"])
    lines.append("🛠️ **Aktivní generované nástroje:** " + (", ".join(act) if act else "(žádné)"))
    return "\n".join(lines)


def _disable(inp: dict, user_id) -> str:
    from core.database import get_session
    from sqlalchemy import text as _t
    kod = (inp.get("kod") or "").strip()
    if not _is_parent(user_id):
        return "🚫 Odpojit nástroj může jen rodič."
    sg = get_session()
    try:
        row = sg.execute(_t("SELECT id FROM g2007.nastroj WHERE kod=:k AND stav_zivota='active' "
                            "AND implementace LIKE 'generated:%'"), {"k": kod}).mappings().first()
        if not row:
            return f"❌ Aktivní generovaný nástroj '{kod}' nenalezen."
        sg.execute(_t("UPDATE g2007.nastroj SET stav_zivota='disabled', updated_at=now() WHERE id=:n"),
                   {"n": row["id"]})
        _audit(sg, "disable", user_id=user_id, nastroj_id=row["id"], detail={"kod": kod, "reason": inp.get("reason")})
        sg.commit()
    finally:
        sg.close()
    _bump_cache()
    return f"🔌 Nástroj '{kod}' odpojen (disabled)."


def _run_as_agent(inp: dict, user_id, conversation_id) -> str:
    """Marti-AI proběhne cíl vlastní agentí smyčkou (Fáze 0 read-only).
    Gate-uje si to samotný martiai_agent_service (flag martiai_agent_enabled)."""
    goal = (inp.get("goal") or inp.get("cil") or "").strip()
    if not goal:
        return "❌ Zadej 'goal' — co mám autonomně proběhnout."
    if not _agent_allowed(user_id):
        return "❌ Agentí režim (run_as_agent) je zatím jen pro admina a rodiče se zapnutým přepínačem v nastavení."
    from modules.conversation.application import martiai_agent_service as MA
    res = MA.run_goal(goal, requested_by_user_id=user_id, conversation_id=conversation_id)
    if not res.get("ok"):
        return f"❌ Agentí běh se nepovedl: {res.get('error')} ({res.get('reason')})"
    hlava = f"🧠 (vlastní agentí smyčka · {res.get('cost_czk')} Kč · {res.get('elapsed_s')}s"
    if res.get("over_per_run_cap"):
        hlava += " · ⚠️ přes per-run strop"
    hlava += ")"
    return f"{hlava}\n\n{res.get('reply')}"


def _dispatch_generated(tool_name, tool_input, user_id, conversation_id) -> Optional[str]:
    from core.database import get_session
    from sqlalchemy import text as _t
    from tool_registry import runtime as RT
    from tool_registry._common import ToolContext
    sg = get_session()
    try:
        row = sg.execute(_t(
            "SELECT kod, selftest_verdikt FROM g2007.nastroj WHERE kod=:k AND stav_zivota='active' "
            "AND implementace LIKE 'generated:%'"), {"k": tool_name}).mappings().first()
    finally:
        sg.close()
    if not row:
        return None
    payload = row["selftest_verdikt"] or {}
    spec = payload.get("spec"); code = payload.get("code")
    if spec and code is not None:
        _ensure_generated_file(tool_name, spec, code)
    from core.database_data import get_data_session as _gds
    ctx = ToolContext(user_id=user_id, conversation_id=conversation_id,
                      entita_id=MARTI_AI_ENTITA_ID, db_session_factory=_gds)
    return RT.execute(tool_name, tool_input, ctx)
