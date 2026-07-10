"""fw.edit_form_binding — DB-řízená vazba přehled(grid_code) → editační jádro(core_id).

Autor: Claude-24 (Kristý), 10. 7. 2026.

PROČ: Editační formulář se na přehled váže přes `FW_EDIT_FORM_REGISTRY`
(statická JS mapa v erp_grid_actions.js: gridCode → editCoreId), která byla
prázdná a runtime nástroj ji nezapíše. Tenhle modul dělá tu vazbu DB-řízenou:
tabulka `fw.edit_form_binding`, kterou frontend při loadu naseeduje do registru.
Statická mapa zůstává jako fallback/override → zpětně kompatibilní.

grid_code = fw.core.code přehledu (list core). core_id = editační jádro (fw.core).

Pojistka (Kristý 10.7.): set_binding nepřepíše existující vazbu potichu —
vrátí {already_bound: X}; přepis jen s force=True.
"""
from __future__ import annotations

from sqlalchemy import text as _t

_DDL = (
    "CREATE TABLE IF NOT EXISTS fw.edit_form_binding ("
    " grid_code text PRIMARY KEY,"
    " core_id bigint NOT NULL REFERENCES fw.core(id) ON DELETE RESTRICT,"
    " created_by_text text,"
    " updated_at timestamptz NOT NULL DEFAULT now()"
    ")"
)


def ensure_table(s) -> None:
    """Idempotentně založí tabulku (owner session — strategie_pg/fw) + zpřístupní
    čtení (mapa grid_code→core není citlivá; čtou ji všichni přihlášení kvůli
    seedu FW_EDIT_FORM_REGISTRY)."""
    s.execute(_t(_DDL))
    try:
        s.execute(_t("GRANT SELECT ON fw.edit_form_binding TO PUBLIC"))
    except Exception:
        pass


def get_all_bindings(s, tolerant: bool = True) -> dict:
    """Vrátí {grid_code: core_id} všech vazeb. tolerant=True → prázdné {}
    když tabulka ještě neexistuje (čtecí session bez DDL práv / před 1. zápisem)."""
    try:
        rows = s.execute(_t(
            "SELECT grid_code, core_id FROM fw.edit_form_binding")).all()
        return {r[0]: int(r[1]) for r in rows}
    except Exception:
        if tolerant:
            return {}
        raise


def get_binding(s, grid_code: str) -> int | None:
    r = s.execute(_t(
        "SELECT core_id FROM fw.edit_form_binding WHERE grid_code = :g"),
        {"g": grid_code}).first()
    return int(r[0]) if r else None


def set_binding(s, grid_code: str, core_id: int, force: bool = False,
                actor: str = "Claude-24 @@COREIMPORT") -> dict:
    """Zapíše/aktualizuje vazbu grid_code → core_id (owner session).

    Guard: pokud grid_code už míří na JINÉ jádro a force=False → NEpřepíše,
    vrátí {"ok": False, "already_bound": <core_id>}. Idempotentní na stejné
    core_id (žádná chyba). Vrací {"ok": True, "replaced": <old|None>}.
    """
    grid_code = (grid_code or "").strip()
    if not grid_code:
        return {"ok": False, "error": "grid_code je prázdné"}
    core_id = int(core_id)
    ensure_table(s)
    # ověř, že cílové jádro existuje (jinak by FK spadl nečitelně)
    if not s.execute(_t("SELECT 1 FROM fw.core WHERE id = :c"), {"c": core_id}).first():
        return {"ok": False, "error": f"fw.core id={core_id} neexistuje"}
    existing = get_binding(s, grid_code)
    if existing is not None and existing != core_id and not force:
        return {"ok": False, "already_bound": existing, "grid_code": grid_code}
    s.execute(_t(
        "INSERT INTO fw.edit_form_binding (grid_code, core_id, created_by_text, updated_at) "
        "VALUES (:g, :c, :a, now()) "
        "ON CONFLICT (grid_code) DO UPDATE SET core_id = EXCLUDED.core_id, "
        "updated_at = now()"),
        {"g": grid_code, "c": core_id, "a": actor})
    return {"ok": True, "grid_code": grid_code, "core_id": core_id,
            "replaced": existing if existing != core_id else None}
