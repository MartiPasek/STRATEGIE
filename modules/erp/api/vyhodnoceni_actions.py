"""ec.* action runner — spouští procedury modulu Vyhodnocení zakázek z UI.

Autor: Claude, 20. 7. 2026.
Endpoint: POST /api/v1/erp/action/run
  body: {"action_code": "...", "id": <zakazka.id>}  (nebo "cislo": "VR...",
         "osoba_id": <id>, "mode": 1|2, "zaks": ["VR...","PR..."])

Whitelist ec.* funkcí (1:1 zrcadlo Centrály). Běží na data_db session s COMMITem
(generický /data/{code} nikdy necommituje → pro side-effecty nepoužitelný).
Role-gate: _require_erp_member. Business chyby vrací funkce jako 'E#...'.
"""
from __future__ import annotations

import json as _json_audit

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import text as _t

from modules.erp.api import router as _r

api_router = _r.api_router

# action_code -> (SQL, druh parametru)
_EC_ACTIONS = {
    "prepocet":          ("SELECT ec.prepocet_vyhodnoceni(:zak)",                 "zak"),
    "priprava":          ("SELECT ec.priprava_vyhodnoceni(:zak)",                 "zak"),
    "vypocet_konstant":  ("SELECT ec.vypocet_konstant(:zak)",                     "zak"),
    "uzavrit":           ("SELECT ec.vyhodnoceni_uzavrit(:zak)",                  "zak"),
    "zrusit":            ("SELECT ec.vyhodnoceni_zrusit(:zak)",                   "zak"),
    "slouci":            ("SELECT ec.slouci_zakazky(CAST(:zaks AS text[]))",      "zaks"),
    "slouci_zrus":       ("SELECT ec.slouci_zakazky_zrus(CAST(:zaks AS text[]))", "zaks"),
    "nastav_sefmontera": ("SELECT ec.nastav_sefmontera(:oid)",                    "oid"),
    "nastav_multif":     ("SELECT ec.nastav_multif(:oid, :mode)",                 "oid_mode"),
    # Modul Příplatky a srážky (Claude-27, 21.7.2026) — p_id + p_cmd (mode 1/2).
    # ⚠️ Od 22.7.2026 v UI NEDOSTUPNÉ (tlačítka vypnutá v ec_pripl_srazky_actions.js):
    # ec.pripl_srazky je živé jednosměrné zrcadlo Centrály, takže zápis sem by při
    # dalším syncu zmizel a do mezd by se nedostal. Endpoint necháváme funkční pro
    # budoucí zapnutí — viz komentář v ec_pripl_srazky_actions.js.
    "pripl_vyplatit":    ("SELECT ec.pripl_srazky_vyplatit(:id, :cmd)",           "id_cmd"),
    "pripl_schvalit":    ("SELECT ec.pripl_srazky_schvalit(:id, :cmd)",           "id_cmd"),
}

# Akce, které sahají na PENÍZE — smí je spustit jen člověk uvedený v ec.akce_opravneni.
# „Uzavřít" vytvoří výplaty (SuperHrubá) v ec.zakazky_finance_zam, „Zrušit" je smaže.
# Ostatní akce (příprava, přepočet, koeficienty, sloučení, šéfmontér) jen počítají
# nebo mění hodnocení — ty zůstávají na běžném přístupu do ERP.
_EC_AKCE_S_OPRAVNENIM = frozenset({"uzavrit", "zrusit"})


@api_router.post("/action/run")
async def ec_action_run(req: Request) -> JSONResponse:
    uid = _r._get_uid(req)
    _r._require_erp_member(uid)

    d = await req.json()
    ac = str(d.get("action_code") or "").strip()
    spec = _EC_ACTIONS.get(ac)
    if not spec:
        return JSONResponse({"ok": False, "error": "neznámá akce (mimo whitelist)"}, status_code=400)
    sql, kind = spec

    from core.database_data import get_data_session as _gds
    session = _gds()
    try:
        # OPRÁVNĚNÍ na citlivé akce (Marti-AI 24.7.2026: „až při napojení reálných dat
        # přidat explicitní oprávnění"; data napojena 5.8.2026). Uzávěrka VYTVÁŘÍ VÝPLATY
        # a zrušení je MAŽE — bez tohohle by to mohl spustit kdokoli z ~20 lidí s přístupem
        # do ERP. Seznam je KONFIGURACE v ec.akce_opravneni, ne kód: přidat/odebrat člověka
        # = jeden řádek, žádný deploy. Zavřeno by default — kdo tam není, nesmí.
        if ac in _EC_AKCE_S_OPRAVNENIM:
            smi = session.execute(_t(
                "SELECT 1 FROM ec.akce_opravneni WHERE akce = :a AND user_id = :u"),
                {"a": ac, "u": uid}).first()
            if not smi:
                return JSONResponse(
                    {"ok": False, "action": ac,
                     "error": "Na tuto akci nemáš oprávnění. Vytváří (nebo maže) výplaty, "
                              "proto ji smí spustit jen pověřená osoba."},
                    status_code=403)

        params: dict = {}
        if kind == "zak":
            zak = str(d.get("cislo") or "").strip()
            if not zak and d.get("id") is not None:
                zak = session.execute(
                    _t("SELECT cislo_zakazky FROM ec.vyhodnoceni_zakazka WHERE id = :id"),
                    {"id": int(d["id"])},
                ).scalar()
            if not zak:
                return JSONResponse({"ok": False, "error": "chybí zakázka (cislo/id)"}, status_code=400)
            params = {"zak": zak}
        elif kind == "zaks":
            zaks = d.get("zaks") or []
            if not isinstance(zaks, list) or not zaks:
                return JSONResponse({"ok": False, "error": "chybí seznam zakázek"}, status_code=400)
            params = {"zaks": [str(z) for z in zaks]}
        elif kind == "oid":
            oid = d.get("osoba_id", d.get("id"))
            params = {"oid": int(oid)}
        elif kind == "oid_mode":
            oid = d.get("osoba_id", d.get("id"))
            params = {"oid": int(oid), "mode": int(d.get("mode") or 1)}
        elif kind == "id_cmd":
            if d.get("id") is None:
                return JSONResponse({"ok": False, "error": "chybí id"}, status_code=400)
            params = {"id": int(d["id"]), "cmd": int(d.get("mode") or d.get("cmd") or 1)}

        res = session.execute(_t(sql), params).scalar()

        # AUDIT (Marti-AI msg 12262, varianta b; C28 5.8.2026). Uzávěrka vytváří výplaty,
        # takže musí být dohledatelné, KDO ji spustil. Uživatele zná jen tahle vrstva —
        # DB funkce ho nevidí. Zápis je ve STEJNÉ transakci jako akce: když projde akce
        # a audit ne, transakce spadne celá a uzávěrka bez záznamu nevznikne.
        # Ukládáme i název volané funkce a parametry, ne jen kdo/kdy.
        _res_s = "" if res is None else str(res)
        session.execute(_t(
            "INSERT INTO ec.akce_audit (uid, akce, funkce, parametry, ok, vysledek) "
            "VALUES (:u, :a, :f, CAST(:p AS jsonb), :ok, :v)"),
            {"u": uid, "a": ac, "f": sql,
             "p": _json_audit.dumps(params, default=str, ensure_ascii=False),
             "ok": not _res_s.startswith("E#"), "v": _res_s[:500]})

        session.commit()
    except Exception as exc:  # noqa: BLE001
        try:
            session.rollback()
        except Exception:
            pass
        return JSONResponse({"ok": False, "error": str(exc)[:400]}, status_code=500)
    finally:
        session.close()

    res_s = "" if res is None else str(res)
    # konvence: funkce vrací 'E#<hláška>' pro business chybu
    if res_s.startswith("E#"):
        return JSONResponse({"ok": False, "error": res_s[2:], "action": ac})
    return JSONResponse({"ok": True, "action": ac, "result": res_s})
