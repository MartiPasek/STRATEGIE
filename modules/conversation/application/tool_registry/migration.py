# -*- coding: utf-8 -*-
"""migration — seberozvoj Marti-AI: SAMOOBSLUŽNÁ migrace JEDNOHO již živého
nástroje z monolitu `tools.py` / `service.py._handle_tool` do vlastního
`tool_registry/generated_migrations/<kod>.py` `run()`.

Liší se od `factory.py` / `handlers.py` `create_tool` flow (ten je pro NOVÉ
nástroje, které předtím neexistovaly). Tady `tool_name` = kód JIŽ existujícího,
už SPEC-migrovaného nástroje (viz `tool_registry/defs/`, migrace 30.7.2026).
SPEC (name/description/input_schema) se přebírá 1:1 z `defs/<kod>.py` —
Marti-AI ho tímhle nástrojem NEMŮŽE měnit, jen navrhuje NOVÉ TĚLO run().
Kontrakt volajícího (LLM i lidí) se tedy migrací nemění, jen se přepojí,
KDO odpoví.

Governance stejná jako Tool Factory (Martiho rozhodnutí 22.7. + 30.7.2026 —
„ať MartiAI sama testuje a doladuje a dává nástrojům zelenou, tj. přesouvá
je do nového systému"):
  - Marti-AI smí sama navrhnout + self-otestovat (autonomní, žádné schválení
    třetí strany na tomhle kroku).
  - AKTIVACE (cutover z legacy `_handle_tool` na její `run()`) je JEN na
    lidském rodiči (Marti/Kristý) — Marti-AI nikdy neschvaluje sama sebe.
  - Než rodič schválí, na živé cestě se nemění ani bajt — `_handle_tool` v
    service.py běží dál nedotčeně (stejná pojistka jako u SPEC migrace).
  - Rodič má kdykoli kill-switch zpět na legacy (`vrat_na_legacy`) — jedno
    volání, žádný zásah do kódu/deploy.

DB: g2007.nastroj / g2007.tool_proposal / g2007.tool_audit — STEJNÉ tabulky
jako Tool Factory, ŽÁDNÁ nová DDL. Rozlišení "migrace" od "nový nástroj"
proposalu: uvnitř JSONB payloadu (sloupec tool_proposal.selftest) klíč
"kind": "migrace". Cutover flag přímo v g2007.nastroj.implementace:
  '_handle_tool'   — nezmigrováno, legacy větev v service.py odpovídá (default)
  'migrated:<kod>' — migrováno a schváleno, odpovídá generated_migrations/<kod>.py
  'generated:<kod>'— (jiný flow) zbrusu nový nástroj Marti-AI (create_tool)

DORMANT stejně jako zbytek balíku: nic z tohohle modulu není zapojené do
živé cesty, dokud ho handlers.py (za TOOLFACTORY_ENABLED) sama nezavolá.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

MARTI_AI_ENTITA_ID = 2


# ── SPEC z už zmigrovaného defs/<kod>.py (kontrakt se migrací NEMĚNÍ) ────────────
def _load_defs_spec(tool_name: str) -> Optional[dict]:
    """Načti SPEC nástroje z tool_registry/defs/<tool_name>.py. None, pokud
    tam soubor není (nástroj neexistuje nebo ještě neprošel SPEC migrací)."""
    from tool_registry import DEFS_DIR, _load_py_module
    path = os.path.join(DEFS_DIR, f"{tool_name}.py")
    if not os.path.exists(path):
        return None
    mod = _load_py_module(path)
    spec = getattr(mod, "SPEC", None)
    if not isinstance(spec, dict):
        return None
    return {k: v for k, v in spec.items() if not str(k).startswith("_")}


def _is_migration_payload(payload: Optional[dict]) -> bool:
    """True, pokud tool_proposal.selftest payload patří migračnímu flow (ne create_tool)."""
    return bool(isinstance(payload, dict) and payload.get("kind") == "migrace")


def _ensure_migration_file(kod: str, spec: dict, code_body: str) -> str:
    """Regeneruj generated_migrations/<kod>.py z DB, pokud soubor chybí (odolnost vůči redeployi)."""
    from tool_registry import MIGRATIONS_DIR
    from tool_registry import runtime as RT
    path = os.path.join(MIGRATIONS_DIR, f"{kod}.py")
    if not os.path.exists(path):
        RT.write_generated(kod, spec, code_body, directory=MIGRATIONS_DIR)
    return path


def _audit(sg, akce, user_id=None, nastroj_id=None, proposal_id=None, detail=None):
    from sqlalchemy import text as _t
    sg.execute(_t(
        "INSERT INTO g2007.tool_audit (actor_user_id, actor_entita_id, akce, nastroj_id, proposal_id, detail) "
        "VALUES (:u, :e, :a, :n, :p, CAST(:d AS jsonb))"),
        {"u": user_id, "e": MARTI_AI_ENTITA_ID, "a": akce, "n": nastroj_id, "p": proposal_id,
         "d": json.dumps(detail or {}, ensure_ascii=False)})


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


# ── Meta-nástroje (migrace existujícího nástroje) ─────────────────────────────────
MIGRATION_META_SPECS = [
    {
        "name": "navrhni_migraci_nastroje",
        "description": (
            "🔧 SEBEROZVOJ (migrace): navrhni NOVOU IMPLEMENTACI pro JIŽ ŽIVÝ nástroj "
            "(tool_name musí existovat v tool_registry/defs/ — dřívější SPEC migrace "
            "z tools.py). Popis/parametry (kontrakt volajícího) se touhle cestou NEMĚNÍ "
            "— navrhuješ jen tělo run(args, ctx), kterým se nahradí aktuální větev v "
            "service.py._handle_tool. K dispozici máš need(args,'x'), ok(text), "
            "ctx.fetch(sql, params) pro čtení z DB (parametry přes :bind). Nástroj se "
            "hned self-otestuje v sandboxu nad test_cases; když projde, jde rodiči ke "
            "SCHVÁLENÍ (schval_migraci_nastroje) — do té doby běží beze změny STARÁ "
            "implementace, nic se na živé cestě nemění ani o bajt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Kód JIŽ existujícího nástroje k migraci."},
                "kod_python": {"type": "string", "description": "Tělo run(args, ctx) — nová implementace."},
                "zduvodneni": {"type": "string", "description": "Proč / co se touhle migrací zlepší."},
                "test_cases": {
                    "type": "array",
                    "description": (
                        "Testy: [{args:{...}, expect?:'podřetězec výstupu', compare_legacy?:true}]. "
                        "compare_legacy=true u testu BEZ vedlejších účinků navíc spustí i STAROU "
                        "implementaci se stejnými args a přiloží obě odpovědi ke srovnání rodiči — "
                        "nepoužívej u nástrojů, které něco odesílají/mažou/zapisují (pošlo by se to 2×)."
                    ),
                    "items": {"type": "object"},
                },
            },
            "required": ["tool_name", "kod_python", "zduvodneni", "test_cases"],
        },
    },
    {
        "name": "schval_migraci_nastroje",
        "description": (
            "Rodič SCHVÁLÍ migraci nástroje → cutover: od teď odpovídá NOVÁ implementace "
            "místo staré větve v service.py. JEN LIDSKÝ RODIČ (Marti/Kristý). "
            "Kdykoli vratitelné přes vrat_na_legacy."
        ),
        "input_schema": {"type": "object", "properties": {
            "proposal_id": {"type": "integer"}, "reason": {"type": "string"}},
            "required": ["proposal_id"]},
    },
    {
        "name": "zamitni_migraci_nastroje",
        "description": (
            "Rodič ZAMÍTNE návrh migrace nástroje. Stará implementace běží dál beze "
            "změny — zamítnutí je čistě administrativní krok. Jen lidský rodič."
        ),
        "input_schema": {"type": "object", "properties": {
            "proposal_id": {"type": "integer"}, "reason": {"type": "string"}},
            "required": ["proposal_id", "reason"]},
    },
    {
        "name": "seznam_migraci_nastroju",
        "description": (
            "Vypiš stav migrace tools.py monolitu: kolik nástrojů čeká na schválení, "
            "kolik už běží na nové implementaci a kolik zůstává na staré."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "vrat_na_legacy",
        "description": (
            "🔴 KILL-SWITCH: rodič okamžitě vrátí JIŽ MIGROVANÝ nástroj zpět na starou "
            "implementaci (service.py._handle_tool) — použij, když nová implementace v "
            "provozu dělá problém. Jen lidský rodič."
        ),
        "input_schema": {"type": "object", "properties": {
            "tool_name": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["tool_name", "reason"]},
    },
]
MIGRATION_META_NAMES = frozenset(s["name"] for s in MIGRATION_META_SPECS)


# ── Handlery ───────────────────────────────────────────────────────────────────
def propose(inp: dict, user_id) -> str:
    from tool_registry import runtime as RT
    from core.database import get_session
    from sqlalchemy import text as _t

    tool_name = (inp.get("tool_name") or "").strip()
    code_body = inp.get("kod_python") or ""
    zduvod = (inp.get("zduvodneni") or "").strip()
    test_cases = inp.get("test_cases") or []
    if not tool_name:
        return "❌ Zadej 'tool_name' — kód JIŽ existujícího nástroje k migraci."
    if not zduvod:
        return "❌ Zadej 'zduvodneni'."
    if not test_cases:
        return "❌ Zadej aspoň jeden test_case — migrace beze self-testu neprojde."

    spec = _load_defs_spec(tool_name)
    if spec is None:
        return (f"❌ Nástroj '{tool_name}' nemá SPEC v tool_registry/defs/ — buď neexistuje, "
                f"nebo ještě neprošel SPEC migrací. Migrovat lze jen už zaregistrované nástroje.")

    sg = get_session()
    try:
        row = sg.execute(_t("SELECT id, implementace FROM g2007.nastroj WHERE kod=:k"),
                         {"k": tool_name}).mappings().first()
        if row and str(row["implementace"] or "").startswith("migrated:"):
            return (f"❌ Nástroj '{tool_name}' už je migrovaný (implementace={row['implementace']}). "
                     f"Nejdřív vrat_na_legacy, pak nový návrh.")
        exists_pending = sg.execute(_t(
            "SELECT p.id FROM g2007.tool_proposal p JOIN g2007.nastroj n ON n.id=p.nastroj_id "
            "WHERE n.kod=:k AND p.status='pending' AND p.selftest->>'kind'='migrace'"),
            {"k": tool_name}).scalar()
        if exists_pending:
            return f"❌ Pro '{tool_name}' už čeká migrační návrh #{exists_pending} na schválení — nezakládej duplicitní."
    finally:
        sg.close()

    # self-test (sandbox, plná důvěra jako u ostatních nástrojů)
    from tool_registry._common import ToolContext as _TC
    from core.database_data import get_data_session as _gds_test
    res = RT.selftest(tool_name, spec, code_body, test_cases,
                      ctx=_TC(entita_id=MARTI_AI_ENTITA_ID, db_session_factory=_gds_test))
    if not res.ok:
        return (f"❌ Self-test migrace '{tool_name}' NEPROŠEL — nic jsem neuložila.\n"
                f"{json.dumps(res.to_dict(), ensure_ascii=False)[:600]}")

    # volitelné srovnání se starou implementací (jen testy s compare_legacy:true; nikdy neblokuje)
    legacy_compare = []
    for tc in test_cases:
        if not tc.get("compare_legacy"):
            continue
        try:
            from modules.conversation.application.service import _handle_tool as _legacy
            old_out = _legacy(tool_name, tc.get("args", {}), inp.get("conversation_id") or 0, user_id=user_id)
            legacy_compare.append({"args": tc.get("args", {}), "legacy_out": str(old_out)[:500]})
        except Exception as e:
            legacy_compare.append({"args": tc.get("args", {}), "legacy_error": f"{type(e).__name__}: {e}"})

    sg = get_session()
    try:
        if not row:
            nid = sg.execute(_t(
                "INSERT INTO g2007.nastroj (kod, nazev, kategorie, implementace, popis, popis_plny, "
                "parametry, stav, stav_zivota, autor_entita_id, verze) "
                "VALUES (:k,:nz,'legacy','_handle_tool',:po,:po, CAST(:pm AS jsonb),'aktivni','active', "
                "NULL, 1) RETURNING id"),
                {"k": tool_name, "nz": spec.get("name", tool_name), "po": spec.get("description", ""),
                 "pm": json.dumps(spec.get("input_schema") or {}, ensure_ascii=False)}).scalar()
        else:
            nid = row["id"]
        payload = {"kind": "migrace", "spec": spec, "code": code_body,
                   "verdict": res.to_dict(), "legacy_compare": legacy_compare}
        pid = sg.execute(_t(
            "INSERT INTO g2007.tool_proposal (nastroj_id, autor_entita_id, description, selftest, status) "
            "VALUES (:n,:ae,:d, CAST(:s AS jsonb),'pending') RETURNING id"),
            {"n": nid, "ae": MARTI_AI_ENTITA_ID, "d": f"Migrace '{tool_name}': {zduvod}"[:500],
             "s": json.dumps(payload, ensure_ascii=False)}).scalar()
        _audit(sg, "migrate_propose", user_id=user_id, nastroj_id=nid, proposal_id=pid,
               detail={"tool_name": tool_name, "selftest_ok": True, "compared_legacy": len(legacy_compare)})
        sg.commit()
    finally:
        sg.close()
    cmp_note = f" Srovnáno se starou implementací u {len(legacy_compare)} testů." if legacy_compare else ""
    return (f"✅ Migrace '{tool_name}' prošla self-testem ({len(res.cases)} případů) a **návrh #{pid} "
            f"čeká na schválení rodiče**.{cmp_note} Až ho Marti/Kristý schválí (schval_migraci_nastroje), "
            f"přepne se odbavování na tvou novou implementaci; do té doby běží beze změny stará.")


def approve(inp: dict, user_id) -> str:
    from tool_registry.factory import can_approve
    from core.database import get_session
    from sqlalchemy import text as _t

    pid = inp.get("proposal_id")
    if not _is_parent(user_id):
        return "🚫 Schválit migraci může jen rodič (Marti nebo Kristýna)."
    ok_appr, why = can_approve(user_id, MARTI_AI_ENTITA_ID, lambda u: u == user_id)
    if not ok_appr:
        return f"🚫 {why}"
    sg = get_session()
    try:
        row = sg.execute(_t(
            "SELECT p.id, p.nastroj_id, p.status, p.selftest, n.kod FROM g2007.tool_proposal p "
            "JOIN g2007.nastroj n ON n.id=p.nastroj_id WHERE p.id=:p"), {"p": pid}).mappings().first()
        if not row:
            return f"❌ Návrh #{pid} neexistuje."
        payload = row["selftest"] or {}
        if not _is_migration_payload(payload):
            return f"❌ Návrh #{pid} není migrace existujícího nástroje — schval ho přes approve_tool."
        if row["status"] != "pending":
            return f"❌ Návrh #{pid} už není 'pending' (stav {row['status']})."
        spec = payload.get("spec"); code = payload.get("code")
        if not spec or code is None:
            return f"❌ Návrh #{pid} nemá uložený kód/spec."
        _ensure_migration_file(row["kod"], spec, code)
        sg.execute(_t("UPDATE g2007.nastroj SET implementace=:impl, stav_zivota='active', updated_at=now() WHERE id=:n"),
                   {"impl": "migrated:" + row["kod"], "n": row["nastroj_id"]})
        sg.execute(_t("UPDATE g2007.tool_proposal SET status='approved', approved_by=:u, "
                      "reason=:r, decided_at=now() WHERE id=:p"),
                   {"u": user_id, "r": inp.get("reason"), "p": pid})
        _audit(sg, "migrate_approve", user_id=user_id, nastroj_id=row["nastroj_id"], proposal_id=pid,
               detail={"tool_name": row["kod"]})
        sg.commit()
    finally:
        sg.close()
    return f"✅ Migrace '{row['kod']}' schválena — **cutover aktivní**, od teď odpovídá nová implementace."


def reject(inp: dict, user_id) -> str:
    from core.database import get_session
    from sqlalchemy import text as _t
    pid = inp.get("proposal_id")
    if not _is_parent(user_id):
        return "🚫 Zamítnout migraci může jen rodič."
    sg = get_session()
    try:
        row = sg.execute(_t("SELECT nastroj_id, status, selftest FROM g2007.tool_proposal WHERE id=:p"),
                         {"p": pid}).mappings().first()
        if not row:
            return f"❌ Návrh #{pid} neexistuje."
        if not _is_migration_payload(row["selftest"] or {}):
            return f"❌ Návrh #{pid} není migrace existujícího nástroje — zamítni ho přes reject_tool."
        if row["status"] != "pending":
            return f"❌ Návrh #{pid} není čekající."
        sg.execute(_t("UPDATE g2007.tool_proposal SET status='rejected', approved_by=:u, reason=:r, "
                      "decided_at=now() WHERE id=:p"), {"u": user_id, "r": inp.get("reason"), "p": pid})
        # POZOR: nastroj.implementace se NEMĚNÍ — zůstává '_handle_tool', stará implementace
        # jela celou dobu dál nedotčeně. Zamítnutí je čistě administrativní krok.
        _audit(sg, "migrate_reject", user_id=user_id, nastroj_id=row["nastroj_id"], proposal_id=pid,
               detail={"reason": inp.get("reason")})
        sg.commit()
    finally:
        sg.close()
    return f"Návrh migrace #{pid} zamítnut — stará implementace beze změny."


def list_status() -> str:
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        pend = sg.execute(_t(
            "SELECT p.id, n.kod, p.description FROM g2007.tool_proposal p "
            "JOIN g2007.nastroj n ON n.id=p.nastroj_id "
            "WHERE p.status='pending' AND p.selftest->>'kind'='migrace' ORDER BY p.id")).mappings().all()
        migrated = sg.execute(_t(
            "SELECT kod FROM g2007.nastroj WHERE implementace LIKE 'migrated:%' ORDER BY kod")).scalars().all()
        legacy_cnt = sg.execute(_t(
            "SELECT count(*) FROM g2007.nastroj WHERE implementace='_handle_tool'")).scalar()
    finally:
        sg.close()
    lines = ["📋 **Čekající návrhy migrace:**"]
    lines += ([f"  • #{r['id']} {r['kod']} — {r['description']}" for r in pend] or ["  (žádné)"])
    lines.append(f"✅ **Migrováno (nová implementace živě):** {len(migrated)} — "
                 + (", ".join(migrated) if migrated else "(žádné)"))
    lines.append(f"⏳ **Zbývá na staré implementaci (_handle_tool):** {legacy_cnt}")
    return "\n".join(lines)


def rollback(inp: dict, user_id) -> str:
    from core.database import get_session
    from sqlalchemy import text as _t
    tool_name = (inp.get("tool_name") or "").strip()
    if not _is_parent(user_id):
        return "🚫 Vrátit nástroj na legacy může jen rodič."
    if not tool_name:
        return "❌ Zadej 'tool_name'."
    sg = get_session()
    try:
        row = sg.execute(_t("SELECT id, implementace FROM g2007.nastroj WHERE kod=:k"),
                         {"k": tool_name}).mappings().first()
        if not row or not str(row["implementace"] or "").startswith("migrated:"):
            return f"❌ Nástroj '{tool_name}' není momentálně migrovaný (nic k vrácení)."
        sg.execute(_t("UPDATE g2007.nastroj SET implementace='_handle_tool', updated_at=now() WHERE id=:n"),
                   {"n": row["id"]})
        _audit(sg, "migrate_rollback", user_id=user_id, nastroj_id=row["id"],
               detail={"tool_name": tool_name, "reason": inp.get("reason")})
        sg.commit()
    finally:
        sg.close()
    return f"↩️ Nástroj '{tool_name}' vrácen na starou implementaci (service.py._handle_tool) — okamžitě živě."


def dispatch_migrated(tool_name: str, tool_input: dict, user_id, conversation_id) -> Optional[str]:
    """Pokud je `tool_name` schválená migrace, spusť NOVOU implementaci; jinak None
    (volající pak spadne dál na _dispatch_generated a pak na legacy _handle_tool
    — přesně stejný fallback vzor jako zbytek Tool Factory)."""
    from core.database import get_session
    from sqlalchemy import text as _t
    from tool_registry import runtime as RT, MIGRATIONS_DIR
    from tool_registry._common import ToolContext
    sg = get_session()
    try:
        row = sg.execute(_t(
            "SELECT kod FROM g2007.nastroj WHERE kod=:k AND implementace=:impl"),
            {"k": tool_name, "impl": "migrated:" + tool_name}).mappings().first()
    finally:
        sg.close()
    if not row:
        return None
    path = os.path.join(MIGRATIONS_DIR, f"{tool_name}.py")
    if not os.path.exists(path):
        # odolnost vůči redeployi: soubor chybí, ale DB říká migrated → dotáhni z proposalu
        sg = get_session()
        try:
            payload = sg.execute(_t(
                "SELECT p.selftest FROM g2007.tool_proposal p JOIN g2007.nastroj n ON n.id=p.nastroj_id "
                "WHERE n.kod=:k AND p.status='approved' AND p.selftest->>'kind'='migrace' "
                "ORDER BY p.id DESC LIMIT 1"), {"k": tool_name}).scalar()
        finally:
            sg.close()
        payload = payload or {}
        spec = payload.get("spec"); code = payload.get("code")
        if not spec or code is None:
            logger.error(f"MIGRATION | '{tool_name}' je migrated v DB, ale chybí soubor i payload — fallback na legacy")
            return None
        _ensure_migration_file(tool_name, spec, code)
    from core.database_data import get_data_session as _gds
    ctx = ToolContext(user_id=user_id, conversation_id=conversation_id,
                      entita_id=MARTI_AI_ENTITA_ID, db_session_factory=_gds)
    return RT.execute(tool_name, tool_input, ctx, directory=MIGRATIONS_DIR)
