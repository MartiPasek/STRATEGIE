"""Docházka po zakázkách — čtení přehledu 109 z Centrály (Claude-26 pro Peťu, 20.7.2026).

Peťa (25.6. mandát) potřebuje v ERP vidět docházku vedenou PO ZAKÁZKÁCH — lidé si
píchají na zakázku a je potřeba to evidovat. Zdroj = `DB_EC.dbo.EC_Dochazka` (Centrála),
1:1 s Delphi přehledem **109 „Docházka"** (`EC_DELPHI_TabObecnyPrehled.Cislo=109`).

Proč vlastní stránka a ne framework grid:
  ERP datagrid načte jednu dávku (page_render posílá `?limit=500`) a filtry i řazení
  dělá v prohlížeči nad staženými řádky — na 400k řádků EC_Dochazka to nestačí a přes
  filtr by se na starší data vůbec nedosáhlo. Tady filtrujeme SERVEROVĚ (jde do SQL
  WHERE), takže je dosažitelná celá historie od 2015 a výchozí pohled ukazuje VŠECHNY
  lidi (Peťa 20.7.: „potřebuji vidět všechny lidi, ne jen přes filtr").

Centrála má v přehledu 109 natvrdo `abs(datediff(month,getdate(),DenZacatek))<3`
(komentář Swobi 10.1.2022: „kvůli rychlosti omezeno. Je třeba udělat zvlášť přehled
na vše") — tohle omezení tady NENÍ, období si volí uživatel.

Sloupec „zdroj" navíc oproti Centrále (Peťa 20.7. — chce vidět, kde se člověk píchnul):
  `LoginFrom`: A = mobilní aplikace, D = tablet, C = ruční zápis v Centrále.
  Mapování shodné s `scripts/migrate_dochazka.py` a importem docházky.

NIC nezapisuje — jen čte přes `eurosoft_strategie_query_raw` (DB_EC read-only).
"""
from __future__ import annotations

import json as _j
import re as _re

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

doch_zak_router = APIRouter(prefix="/api/v1/erp", tags=["dochazka-zakazky"])

# Kdo smí (shodné s viditelností uzlu stromu „🕒 Docházka" / „Docházka po zakázkách"):
# Marti 1, Kristý 11, Šárka 13, Michaela H. 16, Michelle Š. 17, Peťa 18, Honomichl 20,
# Dušan 41, Fajmonová 107, Šafaříková 108, Hrbek 109. Rodič projde vždy.
_DZ_ALLOWED = {1, 11, 13, 16, 17, 18, 20, 41, 107, 108, 109}

# Strop řádků na jedno načtení — pojistka proti „vyber 2015–2026" (400k řádků do
# prohlížeče). UI hlásí, kolik z kolika vidí, a vyzve k zúžení období.
_DZ_MAX_ROWS = 20000

_ZDROJ = {"A": "aplikace", "D": "tablet", "C": "ručně"}


def _dz_can(uid: int | None) -> bool:
    if not uid:
        return False
    if int(uid) in _DZ_ALLOWED:
        return True
    from sqlalchemy import text as _t
    try:
        from core.database_data import get_data_session as _g
        s = _g()
        try:
            return bool(s.execute(_t("SELECT COALESCE(is_marti_parent,false) FROM public.users WHERE id=:u"),
                                  {"u": int(uid)}).scalar())
        finally:
            s.close()
    except Exception:
        return False


def _dz_mcp_rows(sql: str) -> list[dict]:
    """Spustí SELECT na DB_EC přes EUROSOFT MCP a vrátí řádky s lowercase klíči."""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("mcp_unavailable")
    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                             {"sql": sql, "db_name": "DB_EC"}, conversation_id=None)
    r = _j.loads(raw) if isinstance(raw, str) else raw
    rows = []
    if isinstance(r, dict):
        if r.get("ok") is False:
            raise RuntimeError(str(r.get("error"))[:300])
        for k in ("rows", "data", "result", "records"):
            if isinstance(r.get(k), list):
                rows = r[k]
                break
    elif isinstance(r, list):
        rows = r
    return [{(k or "").lower(): v for k, v in d.items()} for d in rows]


def _lit(v: str, maxlen: int = 80) -> str:
    """Bezpečný SQL literál — MCP query_raw nebere bind parametry, skládáme text.
    Zdvojíme apostrofy, uřízneme délku a vyhodíme řídicí znaky (vč. konců řádků,
    aby nešlo rozseknout batch)."""
    s = _re.sub(r"[\x00-\x1f]", " ", str(v or ""))[:maxlen]
    return s.replace("'", "''")


def _den(v: str) -> str | None:
    """Datum z UI → 'YYYY-MM-DD' nebo None. Jiný tvar zahodíme (nedůvěřuj vstupu)."""
    s = (v or "").strip()[:10]
    return s if _re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else None


def _dz_where(p) -> str:
    """WHERE dle voleb uživatele. Prázdná volba = bez omezení (= všichni lidé,
    všechny zakázky). Období se ptá na DenZacatek (indexované, stejně jako Centrála)."""
    w = []
    od, do = _den(p.get("od")), _den(p.get("do"))
    if od:
        w.append("D.DenZacatek >= '" + od + "'")
    if do:
        w.append("D.DenZacatek < DATEADD(day,1,'" + do + "')")
    zam = (p.get("zam") or "").strip()
    if zam.isdigit():
        w.append("D.CisloZam = " + str(int(zam)))
    elif zam:
        w.append("(Z.Jmeno + ' ' + Z.Prijmeni) LIKE '%" + _lit(zam) + "%'")
    zak = (p.get("zakazka") or "").strip()
    if zak:
        w.append("D.CisloZakazky LIKE '%" + _lit(zak, 40) + "%'")
    cin = (p.get("cinnost") or "").strip()
    if cin.isdigit():
        w.append("D.DruhCinnosti = " + str(int(cin)))
    zdroj = (p.get("zdroj") or "").strip().upper()
    if zdroj in ("A", "D", "C"):
        w.append("UPPER(ISNULL(D.LoginFrom,'')) = '" + zdroj + "'")
    elif zdroj == "-":
        w.append("ISNULL(D.LoginFrom,'') NOT IN ('A','D','C')")
    return (" WHERE " + " AND ".join(w)) if w else ""


_DZ_FROM = (" FROM DB_EC.dbo.EC_Dochazka D WITH(NOLOCK)"
            " LEFT OUTER JOIN DB_EC.dbo.TabCisZam Z WITH(NOLOCK) ON D.CisloZam = Z.Cislo"
            " LEFT OUTER JOIN DB_EC.dbo.EC_DilnaCinnosti C WITH(NOLOCK) ON D.DruhCinnosti = C.Cislo"
            " LEFT OUTER JOIN DB_EC.dbo.EC_Dochazka_CinnostiRezie CR WITH(NOLOCK) ON CR.Cislo = D.DruhCinnosti")


@doch_zak_router.get("/app/dochazka-zak/data")
def dochazka_zak_data(req: Request) -> JSONResponse:
    """Řádky docházky po zakázkách. Bez voleb = poslední měsíc, všichni lidé."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    if not _dz_can(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    p = dict(req.query_params)
    try:
        limit = max(1, min(int(p.get("limit") or 2000), _DZ_MAX_ROWS))
    except Exception:
        limit = 2000
    where = _dz_where(p)
    try:
        celkem = 0
        try:
            c = _dz_mcp_rows("SELECT COUNT(*) AS c" + _DZ_FROM + where)
            celkem = int((c[0] or {}).get("c") or 0) if c else 0
        except Exception:
            celkem = -1  # počet se nepovedl (timeout) — řádky přesto zkusíme
        sql = (
            "SELECT TOP " + str(limit) + " D.ID,"
            " D.CisloZakazky, ISNULL(Z.Jmeno + ' ' + Z.Prijmeni,'') AS JmenoPrijmeni, D.CisloZam,"
            " D.DruhCinnosti, ISNULL(C.Nazev,CR.NAZEV) AS CinnostText, D.DenVTydnu,"
            " CONVERT(varchar(19),D.CasZacatek,120) AS CasZacatek,"
            " CONVERT(varchar(19),D.CasKonec,120) AS CasKonec,"
            " D.CasPauza, D.CasBlbost, D.CasRezie,"
            " CAST(ISNULL(D.PozadPomocVed,0) AS int) AS PozadPomocVed,"
            " CAST(ISNULL(D.VedSchvaleno,0) AS int) AS VedSchvaleno,"
            " CAST(ISNULL(D.SefSchvaleno,0) AS int) AS SefSchvaleno,"
            " CAST(ISNULL(D.PrevodPrescasu,0) AS int) AS PrevodPrescasu,"
            " ISNULL(D.ZamPoznamka,'') AS ZamPoznamka, ISNULL(D.VedPoznamka,'') AS VedPoznamka,"
            " D.CasCelkemZakazka, D.CasCelkemVcRezii,"
            " UPPER(ISNULL(D.LoginFrom,'')) AS LoginFrom,"
            " ISNULL(D.Autor,'') AS Autor,"
            " CONVERT(varchar(10),D.DenZacatek,120) AS Den"
            + _DZ_FROM + where +
            " ORDER BY D.DenZacatek DESC, D.CasZacatek DESC"
        )
        rows = _dz_mcp_rows(sql)
    except RuntimeError as e:
        msg = str(e)
        if "mcp_unavailable" in msg:
            return JSONResponse({"ok": False, "error": "Centrála je teď nedostupná — zkus to prosím za chvíli."},
                                status_code=503)
        return JSONResponse({"ok": False, "error": "Nepodařilo se načíst data z Centrály: " + msg[:200]},
                            status_code=502)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": "Chyba při čtení: " + str(e)[:200]}, status_code=500)
    for r in rows:
        r["zdroj"] = _ZDROJ.get((r.get("loginfrom") or "").strip().upper(), "starší záznam")
    return JSONResponse({"ok": True, "rows": rows, "pocet": len(rows),
                         "celkem": celkem, "limit": limit})


@doch_zak_router.get("/app/dochazka-zak/ciselniky")
def dochazka_zak_ciselniky(req: Request) -> JSONResponse:
    """Naplnění roletek — lidé (jen ti s docházkou), činnosti."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    if not _dz_can(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    lide, cinnosti = [], []
    try:
        lide = _dz_mcp_rows(
            "SELECT DISTINCT D.CisloZam, ISNULL(Z.Jmeno + ' ' + Z.Prijmeni,'') AS Jmeno"
            " FROM DB_EC.dbo.EC_Dochazka D WITH(NOLOCK)"
            " LEFT OUTER JOIN DB_EC.dbo.TabCisZam Z WITH(NOLOCK) ON D.CisloZam = Z.Cislo"
            " WHERE D.DenZacatek >= DATEADD(year,-2,GETDATE())"
            " ORDER BY Jmeno")
    except Exception:
        lide = []
    try:
        cinnosti = _dz_mcp_rows(
            "SELECT Cislo, Nazev FROM DB_EC.dbo.EC_DilnaCinnosti WITH(NOLOCK)"
            " UNION SELECT Cislo, NAZEV FROM DB_EC.dbo.EC_Dochazka_CinnostiRezie WITH(NOLOCK)"
            " ORDER BY Nazev")
    except Exception:
        cinnosti = []
    return JSONResponse({"ok": True, "lide": lide, "cinnosti": cinnosti})
