"""fw.edit_form_binding — DB-řízená vazba přehled(grid_code) → editační jádro(core_id).

Autor: Claude-24 (Kristý), 10. 7. 2026. (13.7. rozšířeno o CRUD ops přehledu.)

PROČ: Editační formulář se na přehled váže přes `FW_EDIT_FORM_REGISTRY`
(statická JS mapa v erp_grid_actions.js: gridCode → editCoreId), která byla
prázdná a runtime nástroj ji nezapíše. Tenhle modul dělá tu vazbu DB-řízenou:
tabulka `fw.edit_form_binding`, kterou frontend při loadu naseeduje do registru.
Statická mapa zůstává jako fallback/override → zpětně kompatibilní.

grid_code = fw.core.code přehledu (list core). core_id = editační jádro (fw.core).

CRUD tlačítka (Nový/Oprava/Smazat) zapíná serverový signál `grid_actions`
(router.py page-spec), počítaný z `fw.data_source_op` na data source PŘEHLEDU
(existence op insert/edit/delete). set_binding proto na data source přehledu
DOPLNÍ op edit/insert/delete mířící na jádro — jinak by tlačítka zůstala šedá.
Seznam přehledu jede přes op `select`, ten se nedotkne.

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


def _ensure_prehled_crud_ops(s, grid_code: str, jadro_core_id: int) -> dict:
    """Na data source PŘEHLEDU (grid_code = fw.core.code) doplní op
    edit/insert/delete mířící na jádro → zapne Nový/Oprava/Smazat. Idempotentní.

    Serverový grid_actions (page-spec) čte existenci op insert/edit/delete na
    data source přehledu; edit_core_id = core_id z 'edit' op. Frontend Opravu
    otevírá přes registr (FW_EDIT_FORM_REGISTRY), takže core_id na op je hlavně
    pro edit_core_id/konzistenci. Seznam přehledu jede přes op `select` — ten
    NEmodifikujeme (přidáváme jen edit/insert/delete).
    """
    rep = {"prehled_ds": None, "ops": []}
    # přehled core → aktivní root comp_def s data_source_id
    row = s.execute(_t(
        "SELECT d.data_source_id FROM fw.core c "
        "JOIN fw.comp_def d ON d.core_id = c.id AND d.is_active = true AND d.root = 1 "
        "WHERE c.code = :gc AND d.data_source_id IS NOT NULL "
        "ORDER BY d.sort_order, d.id LIMIT 1"), {"gc": grid_code}).first()
    if not row:
        return rep  # přehled bez data-source rootu (nemělo by nastat) → nic
    ds_id = int(row[0])
    rep["prehled_ds"] = ds_id
    # data_set jádra pro edit (nullable, reuse pro konzistenci s @@COREIMPORT)
    er = s.execute(_t(
        "SELECT data_set_id FROM fw.data_source_op "
        "WHERE core_id = :c AND operation_kind = 'edit' AND data_set_id IS NOT NULL "
        "LIMIT 1"), {"c": jadro_core_id}).first()
    edit_dset = int(er[0]) if er else None
    # edit/insert → míří na jádro (Oprava/Nový = tentýž form, create/edit mode).
    # delete → jen zapínací signál (Smazat maže řádek, neotvírá form) → core NULL.
    specs = [("edit", jadro_core_id, edit_dset, 20),
             ("insert", jadro_core_id, edit_dset, 30),
             ("delete", None, None, 40)]
    for kind, cid, dset, so in specs:
        ex = s.execute(_t(
            "SELECT id FROM fw.data_source_op "
            "WHERE data_source_id = :ds AND operation_kind = :k LIMIT 1"),
            {"ds": ds_id, "k": kind}).first()
        if ex:
            s.execute(_t(
                "UPDATE fw.data_source_op SET core_id = :c, data_set_id = :d WHERE id = :id"),
                {"c": cid, "d": dset, "id": int(ex[0])})
            rep["ops"].append(kind + "(update)")
        else:
            s.execute(_t(
                "INSERT INTO fw.data_source_op "
                "(data_source_id, data_set_id, operation_kind, variant_code, sort_order, is_default, core_id) "
                "VALUES (:ds, :d, :k, 'default', :so, false, :c)"),
                {"ds": ds_id, "d": dset, "k": kind, "so": so, "c": cid})
            rep["ops"].append(kind + "(new)")
    return rep


def set_binding(s, grid_code: str, core_id: int, force: bool = False,
                actor: str = "Claude-24 @@COREIMPORT") -> dict:
    """Zapíše/aktualizuje vazbu grid_code → core_id (owner session) A zapne CRUD
    tlačítka přehledu (op edit/insert/delete na jeho data source).

    Guard: pokud grid_code už míří na JINÉ jádro a force=False → NEpřepíše,
    vrátí {"ok": False, "already_bound": <core_id>}. Idempotentní na stejné
    core_id (žádná chyba). Vrací {"ok": True, "replaced": <old|None>, "crud": {...}}.
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
    # zapni CRUD na přehledu (edit/insert/delete op na jeho data source)
    crud = {}
    try:
        crud = _ensure_prehled_crud_ops(s, grid_code, core_id)
    except Exception as _e:
        crud = {"error": str(_e)[:200]}
    return {"ok": True, "grid_code": grid_code, "core_id": core_id,
            "replaced": existing if existing != core_id else None, "crud": crud}
