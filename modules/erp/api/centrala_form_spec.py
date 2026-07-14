"""fw.centrala_form_spec — framework-neutralni definice formulare z Centraly.

Autor: Claude-24 (Kristy), 14. 7. 2026.

PROC: Skladat kazde jadro rucne do fw.comp_def stromu je krehke a neskaluje na
"spoustu jader". Tenhle modul zachyti KOMPLETNI definici formulare z Centraly do
jedne ciste, na frameworku NEZAVISLE podoby (JSON ve fw.centrala_form_spec).
Tuhle definici pak umi spotrebovat JAKYKOLI renderer (Martiho fw.* i budouci
data-driven renderer) i JAKYKOLI zpusob ukladani (nativni i pres procedury
Centraly). Trvaly zaklad — prezije rozhodnuti o architekture, nic se nezahazuje.
"""
from __future__ import annotations

import json
import re

from sqlalchemy import text as _t

# Neutralni typy (NEzavisle na fw.comp_type — to je smysl specu).
_TYPE_MAP = {1: "label", 2: "text", 3: "checkbox", 4: "memo", 5: "date",
             6: "lookup", 7: "lookup", 9: "file", 11: "grid", 21: "grid"}
_CONTAINER_TYPS = (12, 13, 15, 16)

# CRUD procedury polozek (Kristy 14.7.2026) — ZACHYCENO pro budouci zapis.
# Wiring dodelame az po Martiho navratu; tady je drzime, aby se definice
# neztratila a nemuselo se zacinat znovu.
_GRID_CRUD = {
    602: {
        "insert": "DECLARE    @Ident int,\n        @Message nvarchar(200)\nEXEC    [dbo].[EC_PrijemZbozi_InsertPolozky]\n        @IDDoklad = :IDDoklad,\n        @Ident = @Ident OUTPUT,\n        @RegCis = :RegCis,\n        @Mnozstvi = :Mnozstvi,\n        @Message = @Message OUTPUT\nSELECT    @Ident as N'@Ident',\n        @Message as N'@Message'",
        "update": "DECLARE    @Message nvarchar(200)\nDECLARE @ID INT = :ID\nUPDATE EC_TabSeznamID SET OK = :genVF WHERE ID = @id\nEXEC    [dbo].[EC_PrijemZbozi_UpdatePolozkyGrid]\n        @IDPol = @ID,\n        @Mnozstvi = :Mnozstvi,\n        @MJ = :MJ,\n        @Nazev1 = :Nazev1,\n        @JCbezDaniKC = :JCbezDaniKC,\n        @JCbezDaniVal = :JCbezDaniVal,\n        @CCbezDaniKc = :CCbezDaniKc,\n        @CCbezDaniVal = :CCbezDaniVal,\n        @CisloZakazky = :CisloZakazky,\n        @PotvrzDatDod = :PotvrzDatDod,\n        @Poznamka = :Poznamka,\n        @Popis4 = :Dodano,\n        @EXT_Parametry = NULL,\n        @ObjCislo = :NazevSozNa3,\n        @SlevaZboKmen = :SlevaZboKmen,\n        @SazbaDPH = :SazbaDPH,\n        @Message = @Message OUTPUT \nselect @Message as N'@Message'",
        "delete": "DECLARE @Message nvarchar(100)\nEXEC    [dbo].[EC_PrijemZbozi_SmazPolozkuDokladu]\n        @ID = :ID,\n  @Message = @Message OUTPUT\nSELECT    @Message as N'@Message'",
    },
}

_DDL = (
    "CREATE TABLE IF NOT EXISTS fw.centrala_form_spec ("
    " ec_form_id integer PRIMARY KEY,"
    " code text,"
    " label text,"
    " spec jsonb NOT NULL,"
    " updated_at timestamptz NOT NULL DEFAULT now(),"
    " updated_by_text text"
    ")"
)


def ensure_table(s) -> None:
    """Idempotentne zalozi tabulku + zpristupni cteni (definice neni citliva)."""
    s.execute(_t(_DDL))
    try:
        s.execute(_t("GRANT SELECT ON fw.centrala_form_spec TO PUBLIC"))
    except Exception:
        pass


def _parent_key(par):
    p = (par or "").strip()
    if p.lower().startswith("c") and p[1:].isdigit():
        return int(p[1:])
    return p or "Def"


def build_spec(cen: dict) -> dict:
    """Z Centrala definice (vystup core_import._read_centrala) slozi neutralni spec."""
    from modules.erp.api.core_import import (
        _slug, _GRID_SPEC, _CISELNIK_SQL_FALLBACK)
    comps = cen["comps"]
    nodes = {int(c["cid"]): c for c in comps}

    def as_int(v, d=0):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return d

    def tab_of(cid):
        seen, cur = set(), cid
        while isinstance(cur, int) and cur in nodes and cur not in seen:
            seen.add(cur)
            n = nodes[cur]
            if int(n["typ"]) == 16:
                return (n.get("cap") or "").strip() or ("tab_" + str(cur))
            cur = _parent_key(n.get("par"))
        return None

    tabs = [{"centrala_cid": int(c["cid"]),
             "label": (c.get("cap") or "").strip() or ("tab_" + str(int(c["cid"])))}
            for c in comps if int(c["typ"]) == 16]

    fields = []
    n_lookup = 0
    for c in comps:
        typ = int(c["typ"])
        if typ in _CONTAINER_TYPS or typ in (8, 11, 21):
            continue
        fld = (c.get("fld") or "").strip()
        if not fld:
            continue
        fspec = {"name": fld,
                 "caption": (c.get("cap") or "").strip() or fld,
                 "type": _TYPE_MAP.get(typ, "text"),
                 "order": as_int(c.get("t")) * 10000 + as_int(c.get("l")),
                 "tab": tab_of(_parent_key(c.get("par")))}
        if typ == 6:
            lv = (c.get("lv") or "").strip()
            if lv:
                fc = (c.get("fc") or "").strip()
                flt = None
                if fc and ":" in fc:
                    m = re.search(r":(\w+)", fc)
                    if m:
                        param = m.group(1)
                        col = fc.split("=", 1)[0].strip().split(".")[-1].strip("[]_ ") or param
                        flt = {"param": param, "field": col or param}
                fspec["type"] = "lookup"
                fspec["lookup"] = {
                    "view": int(lv),
                    "id_field": (c.get("lf") or "").strip() or None,
                    "display_field": (c.get("ld") or "").strip() or None,
                    "filter": flt,
                    "source_code": "ciselnik_" + str(int(lv)),
                    "static_sql": int(lv) in _CISELNIK_SQL_FALLBACK,
                }
                n_lookup += 1
        fields.append(fspec)
    fields.sort(key=lambda f: (f.get("tab") or "", f["order"]))

    grids = []
    for c in comps:
        if int(c["typ"]) not in (11, 21):
            continue
        cid = int(c["cid"])
        gs = _GRID_SPEC.get(cid)
        if not gs:
            grids.append({"centrala_cid": cid, "status": "nezmapovano (chybi select/CRUD)"})
            continue
        view = gs["select_view"]
        grids.append({
            "centrala_cid": cid,
            "title": gs.get("title"),
            "select_view": view,
            "source_code": "grid_" + str(view),
            "filter_field": gs.get("filter_field", "ID"),
            "crud": _GRID_CRUD.get(view),
            "files_dir": None,
        })

    files = [{"name": (c.get("fld") or "").strip() or ("file_" + str(int(c["cid"]))),
              "caption": (c.get("cap") or "").strip(),
              "directory": None}
             for c in comps if int(c["typ"]) == 9]

    return {
        "ec_form_id": None,
        "code": _slug(cen["nazev"]),
        "label": cen["nazev"],
        "tabs": tabs,
        "fields": fields,
        "grids": grids,
        "files": files,
        "counts": {"fields": len(fields), "lookups": n_lookup,
                   "grids": len(grids), "tabs": len(tabs), "files": len(files)},
    }


def store(s, ec_form_id: int, spec: dict, actor: str = "Claude-24 @@COREIMPORT") -> dict:
    ensure_table(s)
    spec = dict(spec)
    spec["ec_form_id"] = int(ec_form_id)
    s.execute(_t(
        "INSERT INTO fw.centrala_form_spec (ec_form_id, code, label, spec, updated_at, updated_by_text) "
        "VALUES (:e, :c, :l, CAST(:sp AS jsonb), now(), :a) "
        "ON CONFLICT (ec_form_id) DO UPDATE SET code=EXCLUDED.code, label=EXCLUDED.label, "
        "spec=EXCLUDED.spec, updated_at=now(), updated_by_text=EXCLUDED.updated_by_text"),
        {"e": int(ec_form_id), "c": spec.get("code"), "l": spec.get("label"),
         "sp": json.dumps(spec, ensure_ascii=False), "a": actor})
    return spec["counts"]
