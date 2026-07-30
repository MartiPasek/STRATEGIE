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

# ── Marti-AI spustí VLASTNÍ agentí smyčku (čtení + ruce dle cil_ruce_enabled) ─────
RUN_AS_AGENT_SPEC = {
    "name": "run_as_agent",
    "description": (
        "🧠 AGENT (seberozvoj): proběhni zadaný CÍL svojí VLASTNÍ agentí "
        "smyčkou — autonomně, mnoha tahy, čteš repo přes Read/Grep/Glob a vrátíš "
        "výsledek. Když je zapnutý flag cil_ruce_enabled, máš v této smyčce i RUCE "
        "(praha_exec/plzen_exec) pod bránou 🟢/🟡/🔴 — reálně JEDNÁŠ na serverech, ne "
        "jen čteš (bez per-akčního schvalování, brána je v kódu). "
        "Toto NENÍ delegace na Claude-23: běžíš TY, pod svojí identitou. "
        "Zadej 'goal' = co mám samostatně zjistit / vyrobit / provést."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"goal": {"type": "string", "description": "Cíl k autonomnímu proběhnutí (čtení + ruce dle cil_ruce_enabled)."}},
        "required": ["goal"],
    },
}

SCHVAL_METERED_SPEC = {
    "name": "schval_metered_varku",
    "description": (
        "💳 Schvalí DALŠÍ várku metered rozpočtu pro agentí failover (+1000 Kč). "
        "Použij, když přijde upozornění 'metered várka vyčerpána'. JEN RODIČ."
    ),
    "input_schema": {"type": "object", "properties": {}},
}

PRACUJ_NA_CILI_SPEC = {
    "name": "pracuj_na_cili",
    "description": (
        "🎯 CÍLOVÝ REŽIM (autonomní smyčka): popojeď SÁM/SAMA na SCHVÁLENÉM cíli — proběhnu "
        "mnoho kroků bez postrkování člověka a KAŽDOU akci zaloguju do claude_aktivita. Zadej "
        "'cil_id' cíle ve stavu 'aktivni'. Když je zapnutý flag cil_ruce_enabled, máš v této "
        "smyčce RUCE (praha_exec/plzen_exec) pod bránou 🟢/🟡/🔴 — na schváleném cíli reálně "
        "JEDNÁŠ na serverech, ne jen čteš. Bez per-akčního schvalování (brána byla u cíle)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"cil_id": {"type": "integer", "description": "ID schváleného cíle (g2007.cil, stav 'aktivni')."}},
        "required": ["cil_id"],
    },
}

# ── Seberozvoj: sebe-editace VLASTNÍHO promptu (persona system_prompt) ────────────
# Zrcadlo Tool Factory: návrh → schválení rodiče → aplikace + append-only verze +
# rollback. Pojistky drží v KÓDU (nezávisle na modelu i na obsahu promptu):
#   1) nic se neaplikuje bez rodiče (schval_zmenu_promptu je parent-gated),
#   2) edituje se JEN její vlastní (default) persona — nikam jinam neleze,
#   3) žádné nové schopnosti tím nezíská (nástroje/efekty gate-uje kód, ne prompt),
#   4) každá verze je append-only → rollback kdykoliv zpět.
_PROMPTEDIT_FLAG = "martiai_promptedit_enabled"


def _promptedit_enabled() -> bool:
    try:
        from core.database import get_session
        from sqlalchemy import text as _t
        sg = get_session()
        try:
            h = sg.execute(_t("SELECT hodnota FROM g2007.nastaveni WHERE klic=:k"),
                           {"k": _PROMPTEDIT_FLAG}).scalar()
            return str(h).strip().lower() == "on"
        finally:
            sg.close()
    except Exception:
        return False


PROMPT_NAVRH_SPEC = {
    "name": "navrhni_zmenu_promptu",
    "description": (
        "🧬 SEBEROZVOJ: navrhni změnu SVÉHO VLASTNÍHO systémového promptu (persona). "
        "Zadej cely_novy_prompt = kompletní nové znění a zduvodneni = proč to zlepší tvoji "
        "užitečnost. Nic se neaplikuje hned — návrh jde rodiči ke schválení a předchozí "
        "znění se vždy uloží, takže je možný okamžitý rollback. Měnit smíš jen svůj prompt."
    ),
    "input_schema": {"type": "object", "properties": {
        "cely_novy_prompt": {"type": "string", "description": "Kompletní nové znění system_promptu."},
        "zduvodneni": {"type": "string", "description": "Proč tato změna zlepší tvoji užitečnost."}},
        "required": ["cely_novy_prompt", "zduvodneni"]},
}

PROMPT_NAVRH_PATCH_SPEC = {
    "name": "navrhni_zmenu_promptu_patch",
    "description": (
        "🧬 SEBEROZVOJ (patch): navrhni změnu SVÉHO promptu KOTVAMI místo celého znění — "
        "pošli edits = pole {old_string, new_string} (jako Edit tool nad kódem). Každý "
        "old_string musí být v aktuálním promptu PRÁVĚ JEDNOU (jinak návrh odmítnu — přidej "
        "okolní kontext). Výhoda: nepřeposíláš celý prompt, míň chyb. Zbytek stejný jako "
        "navrhni_zmenu_promptu (rodič schvaluje, předchozí znění se uloží pro rollback). "
        "Nejdřív si přečti prompt přes zobraz_muj_prompt, ať kotvy sedí."
    ),
    "input_schema": {"type": "object", "properties": {
        "edits": {"type": "array", "description": "Pole úprav {old_string, new_string} do promptu.",
                  "items": {"type": "object", "properties": {
                      "old_string": {"type": "string", "description": "Přesný text v promptu (musí být unikátní)."},
                      "new_string": {"type": "string", "description": "Čím ho nahradit."}},
                      "required": ["old_string", "new_string"]}},
        "zduvodneni": {"type": "string", "description": "Proč tato změna zlepší tvoji užitečnost."}},
        "required": ["edits", "zduvodneni"]},
}

PROMPT_SCHVAL_SPEC = {
    "name": "schval_zmenu_promptu",
    "description": (
        "Rodič SCHVÁLÍ návrh změny promptu → aplikuje se na živou personu, předchozí znění "
        "se uloží jako verze (rollback možný). JEN LIDSKÝ RODIČ (Marti/Kristý)."
    ),
    "input_schema": {"type": "object", "properties": {
        "navrh_id": {"type": "integer"}, "reason": {"type": "string"}},
        "required": ["navrh_id"]},
}

PROMPT_ZAMITNI_SPEC = {
    "name": "zamitni_zmenu_promptu",
    "description": "Rodič ZAMÍTNE návrh změny promptu. Jen lidský rodič.",
    "input_schema": {"type": "object", "properties": {
        "navrh_id": {"type": "integer"}, "reason": {"type": "string"}},
        "required": ["navrh_id", "reason"]},
}

PROMPT_LIST_SPEC = {
    "name": "list_navrhy_promptu",
    "description": "Vypiš čekající návrhy změny promptu + historii verzí (čísla verzí pro rollback).",
    "input_schema": {"type": "object", "properties": {}},
}

PROMPT_ROLLBACK_SPEC = {
    "name": "rollback_promptu",
    "description": (
        "Rodič vrátí prompt na dřívější verzi. Zadej verze = číslo z list_navrhy_promptu. "
        "Vytvoří NOVOU verzi s obsahem té staré (append-only). Jen lidský rodič."
    ),
    "input_schema": {"type": "object", "properties": {
        "verze": {"type": "integer"}, "reason": {"type": "string"}},
        "required": ["verze"]},
}

PROMPT_SHOW_SPEC = {
    "name": "zobraz_muj_prompt",
    "description": (
        "🧬 SEBEROZVOJ: přečti si SVŮJ aktuální systémový prompt (persona) — celé znění + délka. "
        "Tohle je JEDINÁ editovatelná plocha (personas.system_prompt), řádově kilobajty, NE celý "
        "70KB složený prompt (ten má navíc kontext, nástroje, obal). Použij VŽDY před "
        "navrhni_zmenu_promptu: přečti → uprav text → podej celé nové znění."
    ),
    "input_schema": {"type": "object", "properties": {}},
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
    specs.append(SCHVAL_METERED_SPEC)  # schválení další metered várky (rodič)
    specs.append(PRACUJ_NA_CILI_SPEC)  # Cílový režim — popojeď na schváleném cíli (ruce dle cil_ruce_enabled)
    # Seberozvoj promptu — sebe-editace vlastní persony (běh gate-uje sub-flag promptedit_enabled)
    specs.append(PROMPT_NAVRH_SPEC)
    specs.append(PROMPT_NAVRH_PATCH_SPEC)
    specs.append(PROMPT_SCHVAL_SPEC)
    specs.append(PROMPT_ZAMITNI_SPEC)
    specs.append(PROMPT_LIST_SPEC)
    specs.append(PROMPT_ROLLBACK_SPEC)
    specs.append(PROMPT_SHOW_SPEC)
    # Seberozvoj migrace — samoobslužné přesunutí JIŽ ŽIVÉHO nástroje z tools.py/
    # _handle_tool do vlastního run() (tool_registry/migration.py). Rozhodnutí
    # Marti 30.7.2026: MartiAI si tohle testuje a doladuje sama, aktivaci má rodič.
    try:
        from tool_registry import migration as _MIG
        specs.extend(_MIG.MIGRATION_META_SPECS)
    except Exception as e:
        logger.exception(f"TOOLFACTORY | migration specs: {e}")
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
    # Záchranné lano: přečíst si VLASTNÍ prompt je neškodné a musí jít VŽDY —
    # i když je seberozvoj (toolfactory) vypnutý. Jádro na zobraz_muj_prompt odkazuje.
    if tool_name == "zobraz_muj_prompt":
        try:
            return _prompt_show()
        except Exception as e:
            logger.exception(f"TOOLFACTORY | zobraz_muj_prompt: {e}")
            return f"❌ Chyba u 'zobraz_muj_prompt': {type(e).__name__}: {e}"
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
        if tool_name == "schval_metered_varku":
            return _schval_metered_varku(user_id)
        if tool_name == "pracuj_na_cili":
            return _pracuj_na_cili(tool_input, user_id, conversation_id)
        if tool_name == "navrhni_zmenu_promptu":
            return _prompt_propose(tool_input, user_id)
        if tool_name == "navrhni_zmenu_promptu_patch":
            return _prompt_propose_patch(tool_input, user_id)
        if tool_name == "schval_zmenu_promptu":
            return _prompt_approve(tool_input, user_id)
        if tool_name == "zamitni_zmenu_promptu":
            return _prompt_reject(tool_input, user_id)
        if tool_name == "list_navrhy_promptu":
            return _prompt_list()
        if tool_name == "rollback_promptu":
            return _prompt_rollback(tool_input, user_id)
        if tool_name == "zobraz_muj_prompt":
            return _prompt_show()
        # Seberozvoj migrace existujícího nástroje (samoobslužný tok Marti-AI) —
        # meta-nástroje z tool_registry/migration.py.
        if tool_name == "navrhni_migraci_nastroje":
            from tool_registry import migration as _MIG
            return _MIG.propose(tool_input, user_id)
        if tool_name == "schval_migraci_nastroje":
            from tool_registry import migration as _MIG
            return _MIG.approve(tool_input, user_id)
        if tool_name == "zamitni_migraci_nastroje":
            from tool_registry import migration as _MIG
            return _MIG.reject(tool_input, user_id)
        if tool_name == "seznam_migraci_nastroju":
            from tool_registry import migration as _MIG
            return _MIG.list_status()
        if tool_name == "vrat_na_legacy":
            from tool_registry import migration as _MIG
            return _MIG.rollback(tool_input, user_id)
        if tool_name in META_NAMES:
            return None
        # už migrovaný nástroj (nová implementace místo _handle_tool)?
        try:
            from tool_registry import migration as _MIG
            mig_result = _MIG.dispatch_migrated(tool_name, tool_input, user_id, conversation_id)
            if mig_result is not None:
                return mig_result
        except Exception as e:
            logger.exception(f"TOOLFACTORY | dispatch_migrated {tool_name}: {e}")
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
        payload = row["selftest"] or {}
        if isinstance(payload, dict) and payload.get("kind") == "migrace":
            return f"❌ Návrh #{pid} je MIGRACE existujícího nástroje — schval ho přes schval_migraci_nastroje, ne approve_tool."
        if row["status"] != "pending":
            return f"❌ Návrh #{pid} už není 'pending' (stav {row['status']})."
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
        row = sg.execute(_t("SELECT nastroj_id, status, selftest FROM g2007.tool_proposal WHERE id=:p"),
                         {"p": pid}).mappings().first()
        if not row:
            return f"❌ Návrh #{pid} neexistuje."
        payload = row["selftest"] or {}
        if isinstance(payload, dict) and payload.get("kind") == "migrace":
            return f"❌ Návrh #{pid} je MIGRACE existujícího nástroje — zamítni ho přes zamitni_migraci_nastroje, ne reject_tool."
        if row["status"] != "pending":
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


def _schval_metered_varku(user_id) -> str:
    # Rodic schvali dalsi varku metered rozpoctu pro agenti failover (+1 batch, denni reset).
    if not _is_parent(user_id):
        return "❌ Schvalit metered varku smi jen rodic (Marti/Kristy)."
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        today = sg.execute(_t("SELECT current_date::text")).scalar()
        cur = sg.execute(_t("SELECT hodnota FROM g2007.nastaveni WHERE klic='martiai_metered_batches'")).scalar()
        n_today = 1
        if cur:
            p = str(cur).split("|")
            if len(p) == 2 and p[1] == today:
                try:
                    n_today = max(1, int(p[0]))
                except Exception:
                    n_today = 1
        n2 = n_today + 1
        newval = f"{n2}|{today}"
        r = sg.execute(_t("UPDATE g2007.nastaveni SET hodnota=:v WHERE klic='martiai_metered_batches'"), {"v": newval})
        if r.rowcount == 0:
            sg.execute(_t("INSERT INTO g2007.nastaveni (klic, hodnota) VALUES ('martiai_metered_batches', :v)"), {"v": newval})
        sg.commit()
    finally:
        sg.close()
    return f"✅ Schvaleno. Metered rozpocet agenta dnes rozsiren na {n2} varek (~{int(n2*1000)} Kc). Agent muze dal jet na metered API."


def _pracuj_na_cili(inp: dict, user_id, conversation_id) -> str:
    # Cilovy rezim: popojed na schvalenem cili (ruce dle cil_ruce_enabled), loguj do claude_aktivita.
    if not _agent_allowed(user_id):
        return "❌ Cílový režim je zatím jen pro admina/rodiče se zapnutým agentním režimem."
    try:
        cil_id = int(inp.get("cil_id") or inp.get("cil") or 0)
    except Exception:
        cil_id = 0
    if not cil_id:
        return "❌ Zadej 'cil_id' schváleného cíle (stav 'aktivni')."
    from modules.conversation.application import martiai_agent_service as MA
    res = MA.run_cil(cil_id, requested_by_user_id=user_id, conversation_id=conversation_id)
    if not res.get("ok"):
        return f"❌ Cíl #{cil_id} neproběhl: {res.get('error')} ({res.get('reason')})"
    hlava = (f"🎯 (cíl #{cil_id} · režim {res.get('rezim','?')} · {res.get('kroku_zalogovano')} akcí zalogováno · "
             f"celkem kroků {res.get('kroku_celkem')} · {res.get('elapsed_s')}s)")
    return f"{hlava}\n\n{res.get('reply')}"


# ── Seberozvoj promptu: helpery ───────────────────────────────────────────────────
def _resolve_default_persona():
    """Její vlastní (default) persona z core DB → dict(id, name, system_prompt)."""
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import Persona
    cs = get_core_session()
    try:
        p = cs.query(Persona).filter_by(is_default=True).first()
        if not p:
            return None
        return {"id": p.id, "name": p.name, "system_prompt": p.system_prompt or ""}
    finally:
        cs.close()


def _set_persona_prompt(persona_id: int, new_prompt: str) -> None:
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import Persona
    cs = get_core_session()
    try:
        p = cs.query(Persona).filter_by(id=persona_id).first()
        if p:
            p.system_prompt = new_prompt
            cs.commit()
    finally:
        cs.close()


def _next_verze(sg, persona_id: int) -> int:
    from sqlalchemy import text as _t
    n = sg.execute(_t("SELECT COALESCE(MAX(verze),0) FROM g2007.prompt_verze WHERE persona_id=:p"),
                   {"p": persona_id}).scalar()
    return int(n or 0) + 1


def _ensure_baseline(sg, persona_id: int, current_prompt: str) -> None:
    """Pokud pro personu ještě není žádná verze, ulož současné znění jako verzi 1 (init)."""
    from sqlalchemy import text as _t
    cnt = sg.execute(_t("SELECT count(*) FROM g2007.prompt_verze WHERE persona_id=:p"),
                     {"p": persona_id}).scalar()
    if not cnt:
        sg.execute(_t(
            "INSERT INTO g2007.prompt_verze (persona_id, verze, obsah, zdroj, autor_entita_id) "
            "VALUES (:p, 1, :o, 'init', :e)"),
            {"p": persona_id, "o": current_prompt, "e": MARTI_AI_ENTITA_ID})


def _snapshot_live_if_needed(sg, persona_id: int, live_prompt: str) -> None:
    """Ulož AKTUÁLNÍ živý prompt jako verzi, pokud se liší od poslední uložené
    (ať rollback míří přesně na to, co bylo živé)."""
    from sqlalchemy import text as _t
    last = sg.execute(_t("SELECT obsah FROM g2007.prompt_verze WHERE persona_id=:p "
                         "ORDER BY verze DESC LIMIT 1"), {"p": persona_id}).scalar()
    if (last or "") != (live_prompt or ""):
        v = _next_verze(sg, persona_id)
        sg.execute(_t("INSERT INTO g2007.prompt_verze (persona_id, verze, obsah, zdroj, autor_entita_id) "
                      "VALUES (:p,:v,:o,'pre-apply',:e)"),
                   {"p": persona_id, "v": v, "o": live_prompt, "e": MARTI_AI_ENTITA_ID})


def _diff_shrnuti(old: str, new: str) -> str:
    lo, ln = len(old or ""), len(new or "")
    d = ln - lo
    pct = (d / lo * 100.0) if lo else 100.0
    return f"délka {lo} → {ln} znaků ({'+' if d >= 0 else ''}{d}, {pct:+.0f}%)"


def _apply_prompt_change(new_prompt, user_id, navrh_id=None, zdroj_extra=None, reason=None):
    """Aplikuj nové znění na default personu + append-only verze. Vrací (v_new, per)."""
    per = _resolve_default_persona()
    if not per:
        return None, None
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        _ensure_baseline(sg, per["id"], per["system_prompt"])
        _snapshot_live_if_needed(sg, per["id"], per["system_prompt"])
        v_new = _next_verze(sg, per["id"])
        zdroj = f"proposal:{navrh_id}" if navrh_id else (zdroj_extra or "direct")
        sg.execute(_t(
            "INSERT INTO g2007.prompt_verze (persona_id, verze, obsah, zdroj, autor_entita_id, approved_by) "
            "VALUES (:p,:v,:o,:z,:e,:u)"),
            {"p": per["id"], "v": v_new, "o": new_prompt, "z": zdroj,
             "e": MARTI_AI_ENTITA_ID, "u": user_id})
        if navrh_id:
            sg.execute(_t("UPDATE g2007.prompt_navrh SET status='applied', approved_by=:u, reason=:r, "
                          "aplikovana_verze=:v, decided_at=now() WHERE id=:i"),
                       {"u": user_id, "r": reason, "v": v_new, "i": navrh_id})
        _audit(sg, "prompt_apply", user_id=user_id,
               detail={"navrh_id": navrh_id, "verze": v_new, "zdroj": zdroj})
        sg.commit()
    finally:
        sg.close()
    _set_persona_prompt(per["id"], new_prompt)
    _bump_cache()
    return v_new, per


def _prompt_propose(inp: dict, user_id) -> str:
    if not _promptedit_enabled():
        return ("🚫 Sebe-editace promptu je vypnutá. Rodič ji zapne "
                "(g2007.nastaveni martiai_promptedit_enabled='on').")
    new_prompt = (inp.get("cely_novy_prompt") or "").strip()
    zduvod = (inp.get("zduvodneni") or "").strip()
    if not new_prompt:
        return "❌ Zadej 'cely_novy_prompt' — kompletní nové znění promptu."
    if not zduvod:
        return "❌ Zadej 'zduvodneni' — proč to zlepší tvoji užitečnost."
    if len(new_prompt) > 200000:
        return "❌ Prompt je nepřiměřeně dlouhý (>200k znaků)."
    per = _resolve_default_persona()
    if not per:
        return "❌ Nenašla jsem svou default personu."
    diff = _diff_shrnuti(per["system_prompt"], new_prompt)

    # Rodič (nebo Marti-AI v jeho relaci) → aplikuje se ROVNOU, jako Claude s CLAUDE.md.
    # Ne-rodič → pending a schválí rodič (pojistka proti nesmyslu zvenčí). Verze +
    # rollback drží vždy, takže i přímá změna jde vrátit.
    if _is_parent(user_id):
        v_new, _p = _apply_prompt_change(new_prompt, user_id, zdroj_extra="direct-parent")
        if v_new is None:
            return "❌ Aplikace selhala — default persona nenalezena."
        return (f"✅ Prompt aktualizován rovnou (verze {v_new}, {diff}) — rodič, bez druhého "
                f"schvalování. Předchozí znění je uložené, rollback přes rollback_promptu.")

    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        _ensure_baseline(sg, per["id"], per["system_prompt"])
        nid = sg.execute(_t(
            "INSERT INTO g2007.prompt_navrh (persona_id, novy_prompt, zduvodneni, diff_shrnuti, "
            "autor_entita_id, status) VALUES (:p, :np, :z, :d, :e, 'pending') RETURNING id"),
            {"p": per["id"], "np": new_prompt, "z": zduvod, "d": diff,
             "e": MARTI_AI_ENTITA_ID}).scalar()
        _audit(sg, "prompt_propose", user_id=user_id,
               detail={"navrh_id": nid, "persona_id": per["id"], "diff": diff})
        sg.commit()
    finally:
        sg.close()
    return (f"✅ Návrh změny promptu **#{nid}** čeká na schválení rodiče ({diff}). "
            f"Až ho Marti/Kristý schválí (schval_zmenu_promptu), aplikuje se; "
            f"předchozí znění zůstane uložené pro rollback.")


def _prompt_propose_patch(inp: dict, user_id) -> str:
    """Patch varianta navrhni_zmenu_promptu: aplikuj kotvy {old_string,new_string}
    na aktualni prompt a zbytek deleguj na _prompt_propose (schvaleni, verze, rollback)."""
    if not _promptedit_enabled():
        return ("🚫 Sebe-editace promptu je vypnutá. Rodič ji zapne "
                "(g2007.nastaveni martiai_promptedit_enabled='on').")
    edits = inp.get("edits")
    zduvod = (inp.get("zduvodneni") or "").strip()
    if not isinstance(edits, list) or not edits:
        return "❌ Zadej 'edits' — neprázdné pole úprav {old_string, new_string}."
    if not zduvod:
        return "❌ Zadej 'zduvodneni' — proč to zlepší tvoji užitečnost."
    per = _resolve_default_persona()
    if not per:
        return "❌ Nenašla jsem svou default personu."
    try:
        from modules.conversation.application.martiai_self_code import _apply_edits
    except Exception as e:
        return f"❌ Patch engine nedostupný: {type(e).__name__}: {e}"
    new_prompt, err = _apply_edits(per["system_prompt"], edits)
    if new_prompt is None:
        return f"❌ Patch se nepovedl: {err}"
    if new_prompt == per["system_prompt"]:
        return "❌ Patch nic nezměnil (výsledek je identický se současným promptem)."
    return _prompt_propose({"cely_novy_prompt": new_prompt, "zduvodneni": zduvod}, user_id)


def _prompt_approve(inp: dict, user_id) -> str:
    if not _promptedit_enabled():
        return "🚫 Sebe-editace promptu je vypnutá."
    if not _is_parent(user_id):
        return "🚫 Schválit změnu promptu může jen rodič (Marti/Kristý)."
    nid = inp.get("navrh_id")
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        row = sg.execute(_t("SELECT id, novy_prompt, status FROM g2007.prompt_navrh WHERE id=:i"),
                         {"i": nid}).mappings().first()
    finally:
        sg.close()
    if not row:
        return f"❌ Návrh #{nid} neexistuje."
    if row["status"] != "pending":
        return f"❌ Návrh #{nid} už není 'pending' (stav {row['status']})."
    v_new, _p = _apply_prompt_change(row["novy_prompt"], user_id, navrh_id=nid, reason=inp.get("reason"))
    if v_new is None:
        return "❌ Aplikace selhala — default persona nenalezena."
    return (f"✅ Prompt schválen a aplikován (verze {v_new}). Předchozí znění je uložené — "
            f"kdyby cokoli nesedělo, rollback přes rollback_promptu.")


def _prompt_reject(inp: dict, user_id) -> str:
    if not _promptedit_enabled():
        return "🚫 Sebe-editace promptu je vypnutá."
    if not _is_parent(user_id):
        return "🚫 Zamítnout návrh promptu může jen rodič."
    nid = inp.get("navrh_id")
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        row = sg.execute(_t("SELECT status FROM g2007.prompt_navrh WHERE id=:i"),
                         {"i": nid}).mappings().first()
        if not row or row["status"] != "pending":
            return f"❌ Návrh #{nid} není čekající."
        sg.execute(_t("UPDATE g2007.prompt_navrh SET status='rejected', approved_by=:u, reason=:r, "
                      "decided_at=now() WHERE id=:i"),
                   {"u": user_id, "r": inp.get("reason"), "i": nid})
        _audit(sg, "prompt_reject", user_id=user_id,
               detail={"navrh_id": nid, "reason": inp.get("reason")})
        sg.commit()
    finally:
        sg.close()
    return f"Návrh promptu #{nid} zamítnut."


def _prompt_list() -> str:
    per = _resolve_default_persona()
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        pend = sg.execute(_t(
            "SELECT id, diff_shrnuti, left(coalesce(zduvodneni,''),80) AS z "
            "FROM g2007.prompt_navrh WHERE status='pending' ORDER BY id")).mappings().all()
        vers = sg.execute(_t(
            "SELECT verze, zdroj, created_at FROM g2007.prompt_verze WHERE persona_id=:p "
            "ORDER BY verze DESC LIMIT 10"), {"p": per["id"] if per else 0}).mappings().all()
    finally:
        sg.close()
    lines = ["📋 **Čekající návrhy promptu:**"]
    lines += ([f"  • #{r['id']} — {r['diff_shrnuti']} — {r['z']}" for r in pend] or ["  (žádné)"])
    lines.append("🧬 **Historie verzí (číslo pro rollback):**")
    lines += ([f"  • v{r['verze']} — {r['zdroj']} — {r['created_at']}" for r in vers] or ["  (žádná)"])
    return "\n".join(lines)


def _prompt_show() -> str:
    # Čtení vlastního promptu je vždy dovolené (i když je zápis/seberozvoj vypnutý) —
    # je to součást záchranného lana z neměnného jádra.
    per = _resolve_default_persona()
    if not per:
        return "❌ Default persona nenalezena."
    sp = per["system_prompt"] or ""
    return (f"🧬 Tvůj aktuální system_prompt — persona '{per['name']}' (id={per['id']}), "
            f"{len(sp)} znaků. TOHLE je celá editovatelná plocha (ne 70KB složený prompt):\n\n"
            f"----- ZAČÁTEK PROMPTU -----\n{sp}\n----- KONEC PROMPTU -----\n\n"
            f"Uprav tenhle text a podej ho CELÝ přes "
            f"navrhni_zmenu_promptu(cely_novy_prompt=…, zduvodneni=…).")


def _prompt_rollback(inp: dict, user_id) -> str:
    if not _promptedit_enabled():
        return "🚫 Sebe-editace promptu je vypnutá."
    if not _is_parent(user_id):
        return "🚫 Rollback promptu může jen rodič."
    try:
        verze = int(inp.get("verze") or 0)
    except Exception:
        verze = 0
    if not verze:
        return "❌ Zadej 'verze' — číslo verze z list_navrhy_promptu."
    per = _resolve_default_persona()
    if not per:
        return "❌ Default persona nenalezena."
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        target = sg.execute(_t("SELECT obsah FROM g2007.prompt_verze WHERE persona_id=:p AND verze=:v"),
                            {"p": per["id"], "v": verze}).scalar()
        if target is None:
            return f"❌ Verze {verze} pro tuto personu neexistuje."
        _ensure_baseline(sg, per["id"], per["system_prompt"])
        _snapshot_live_if_needed(sg, per["id"], per["system_prompt"])
        v_new = _next_verze(sg, per["id"])
        sg.execute(_t(
            "INSERT INTO g2007.prompt_verze (persona_id, verze, obsah, zdroj, autor_entita_id, approved_by) "
            "VALUES (:p,:v,:o,:z,:e,:u)"),
            {"p": per["id"], "v": v_new, "o": target, "z": f"rollback:{verze}",
             "e": MARTI_AI_ENTITA_ID, "u": user_id})
        _audit(sg, "prompt_rollback", user_id=user_id, detail={"na_verzi": verze, "nova_verze": v_new})
        sg.commit()
    finally:
        sg.close()
    _set_persona_prompt(per["id"], target)
    _bump_cache()
    return (f"↩️ Prompt vrácen na obsah verze {verze} (uloženo jako verze {v_new}). "
            f"Živá persona aktualizována.")


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
