"""
OZ mirror (Marti 2.7.2026) — zrcadlení EUROSOFT přehledů (Oběh zboží) na cloud PG.

Doktrína (Marti): NEMIGRUJEME na nové schéma. Každý přehledový MSSQL dotaz běží
tam, kam patří (on-prem DB_EC přes MCP), a jeho VÝSLEDEK se nasype do ploché
produkční PG tabulky `tenant.oz_<...>`. Sloupce = aliasy dotazu (čisté názvy
zadarmo). FW přehled pak čte `SELECT * FROM tenant.oz_<...>` (PG, connection 1).

Schéma cílové tabulky se odvodí z `sp_describe_first_result_set` (běží přes MCP,
NE přes bridge — bridge EXEC=write nevrací řádky).
"""
from __future__ import annotations

import json as _j


def _mcp_query(sql: str, db: str = "DB_EC"):
    """Spustí libovolný SQL na EUROSOFT MSSQL přes MCP, vrátí list dict řádků."""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP nedostupný")
    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                             {"sql": sql, "db_name": db}, conversation_id=None)
    r = _j.loads(raw) if isinstance(raw, str) else raw
    if isinstance(r, dict):
        if r.get("ok") is False:
            raise RuntimeError(str(r.get("error") or r)[:300])
        return r.get("rows") or []
    return r or []


def _pg_type(mssql_type: str) -> str:
    """MSSQL system_type_name (např. 'numeric(19,2)', 'nvarchar(255)') → PG typ."""
    t = (mssql_type or "").strip().lower()
    base = t.split("(")[0].strip()
    if base in ("int", "integer"):
        return "integer"
    if base in ("bigint",):
        return "bigint"
    if base in ("smallint", "tinyint"):
        return "smallint"
    if base in ("bit",):
        return "boolean"
    if base in ("numeric", "decimal", "money", "smallmoney"):
        # zachovej přesnost pokud je
        if "(" in t:
            return "numeric" + t[t.index("("):]
        return "numeric"
    if base in ("float", "real"):
        return "double precision"
    if base in ("date",):
        return "date"
    if base in ("datetime", "datetime2", "smalldatetime", "datetimeoffset"):
        return "timestamp"
    if base in ("time",):
        return "time"
    if base in ("uniqueidentifier",):
        return "text"
    if base in ("varbinary", "binary", "image", "timestamp", "rowversion"):
        return "text"  # bin/rowversion nezrcadlíme binárně
    # nvarchar/varchar/nchar/char/text/ntext/xml a cokoli ostatní
    return "text"


def describe(sql: str):
    """sp_describe_first_result_set → [{name, pg_type, ord}] v pořadí sloupců."""
    esc = sql.replace("'", "''")
    rows = _mcp_query("EXEC sp_describe_first_result_set N'%s', NULL, 0" % esc)
    cols = []
    for r in rows:
        nm = r.get("name") if isinstance(r, dict) else None
        st = r.get("system_type_name") if isinstance(r, dict) else None
        ordv = r.get("column_ordinal") if isinstance(r, dict) else None
        if not nm:
            # bezejmenný sloupec (chybějící alias) — pojmenuj
            nm = "col_%s" % (ordv or len(cols) + 1)
        cols.append({"name": str(nm), "pg_type": _pg_type(st or ""), "ord": ordv or (len(cols) + 1)})
    return cols


def _qi(name: str) -> str:
    """Bezpečný quoted identifier pro PG."""
    return '"' + str(name).replace('"', '""') + '"'


def create_table(oz_table: str, cols: list, tenant_id: int = 2, drop: bool = True):
    """Vytvoří tenant.<oz_table> podle sloupců (drop+create). Vrací DDL."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    coldefs = ", ".join("%s %s" % (_qi(c["name"]), c["pg_type"]) for c in cols)
    ddl = "CREATE TABLE tenant.%s (%s)" % (oz_table, coldefs)
    s = get_data_session()
    try:
        if drop:
            s.execute(_t("DROP TABLE IF EXISTS tenant.%s" % oz_table))
        s.execute(_t(ddl))
        s.execute(_t('GRANT ALL ON tenant.%s TO strategie, "Marti-AI"' % oz_table))
        s.commit()
    finally:
        s.close()
    return ddl


def _to_val(v, pg_type):
    if v is None or v == "":
        # prázdný string u n/ časových typů = NULL
        if pg_type != "text":
            return None
        return v
    return v


def fill(oz_table: str, sql: str, cols: list, tenant_id: int = 2, batch: int = 500):
    """Naplní tenant.<oz_table> výsledkem MSSQL dotazu (TRUNCATE + INSERT)."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    rows = _mcp_query(sql)
    names = [c["name"] for c in cols]
    types = {c["name"]: c["pg_type"] for c in cols}
    collist = ", ".join(_qi(n) for n in names)
    params = ", ".join(":p%d" % i for i in range(len(names)))
    ins = "INSERT INTO tenant.%s (%s) VALUES (%s)" % (oz_table, collist, params)
    s = get_data_session()
    vloz = 0
    chyb = 0
    prvni = None
    try:
        s.execute(_t("TRUNCATE tenant.%s" % oz_table))
        buf = []

        def _flush(b):
            nonlocal vloz, chyb, prvni
            if not b:
                return
            try:
                s.execute(_t(ins), b)
                s.commit()
                vloz += len(b)
            except Exception as e:  # noqa: BLE001
                s.rollback()
                # per-row fallback
                for one in b:
                    try:
                        s.execute(_t(ins), one)
                        s.commit()
                        vloz += 1
                    except Exception as e2:  # noqa: BLE001
                        s.rollback()
                        chyb += 1
                        if prvni is None:
                            prvni = str(e2)[:200]

        for r in rows:
            d = r if isinstance(r, dict) else {}
            row = {}
            for i, n in enumerate(names):
                val = d.get(n)
                if val is None:
                    # sp_describe názvy sedí na klíče query_raw; kdyby ne, zkus case-insensitive
                    for k in d.keys():
                        if k.lower() == n.lower():
                            val = d[k]
                            break
                row["p%d" % i] = _to_val(val, types[n])
            buf.append(row)
            if len(buf) >= batch:
                _flush(buf)
                buf = []
        _flush(buf)
        return {"ok": True, "vlozeno": vloz, "chyb": chyb, "prvni_chyba": prvni, "zdroj_radku": len(rows)}
    finally:
        s.close()


def _ensure_def_table(tenant_id: int = 2):
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        s.execute(_t(
            "CREATE TABLE IF NOT EXISTS tenant.oz_mirror_def ("
            "oz_table text PRIMARY KEY, fw_code text, sql_mssql text, "
            "last_sync_at timestamp, last_rows int, updated_at timestamp DEFAULT now())"))
        # Mód zrcadlení (Marti 6.7.2026): DEL = celá tabulka pryč+znovu (výjimka), RO = delta,
        # Helios vlastní řádek (jen čteme), RW = delta, my píšeme svoje sloupce (saldo/příznaky) →
        # update jen Helios polí, naše chráněná. ALTER běží jako strategie=vlastník (Marti-AI nesmí).
        s.execute(_t("ALTER TABLE tenant.oz_mirror_def ADD COLUMN IF NOT EXISTS mode varchar(6) DEFAULT 'DEL'"))
        s.execute(_t('GRANT ALL ON tenant.oz_mirror_def TO strategie, "Marti-AI"'))
        s.commit()
    finally:
        s.close()


def mirror(fw_code: str, oz_table: str, tenant_id: int = 2, repoint: bool = True):
    """Kompletní zrcadlení: vezme MSSQL dotaz z fw.data_set[fw_code], odvodí schéma,
    vytvoří tenant.<oz_table>, naplní, uloží def a přepne fw.data_set na PG."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    _ensure_def_table(tenant_id)
    s = get_data_session()
    try:
        src = s.execute(_t(
            "SELECT dset.sql_text, dset.db_connection_id, dset.id AS dsid "
            "FROM fw.data_source ds JOIN fw.data_source_op op ON op.data_source_id=ds.id "
            "JOIN fw.data_set dset ON dset.id=op.data_set_id "
            "WHERE ds.code=:c AND op.operation_kind='select'"),
            {"c": fw_code}).mappings().first()
    finally:
        s.close()
    if not src:
        return {"ok": False, "error": "fw.data_set pro %s nenalezen" % fw_code}
    sql_mssql = src["sql_text"]
    if "tenant." in sql_mssql.lower() and "from tenant.oz_" in sql_mssql.lower():
        # už přepnuto na PG — vezmi uloženou MSSQL definici
        s2 = get_data_session()
        try:
            saved = s2.execute(_t(
                "SELECT sql_mssql FROM tenant.oz_mirror_def "
                "WHERE fw_code=:f OR oz_table=:o ORDER BY updated_at DESC LIMIT 1"),
                {"f": fw_code, "o": oz_table}).scalar()
        finally:
            s2.close()
        if saved:
            sql_mssql = saved
        else:
            return {"ok": False, "error": "data_set už přepnut na PG a chybí uložený MSSQL def"}

    cols = describe(sql_mssql)
    if not cols:
        return {"ok": False, "error": "sp_describe nevrátil sloupce"}
    create_table(oz_table, cols, tenant_id=tenant_id, drop=True)
    res = fill(oz_table, sql_mssql, cols, tenant_id=tenant_id)

    s3 = get_data_session()
    try:
        s3.execute(_t(
            "INSERT INTO tenant.oz_mirror_def(oz_table,fw_code,sql_mssql,last_sync_at,last_rows) "
            "VALUES(:o,:f,:q,now(),:n) ON CONFLICT (oz_table) DO UPDATE SET "
            "fw_code=EXCLUDED.fw_code, sql_mssql=EXCLUDED.sql_mssql, last_sync_at=now(), "
            "last_rows=EXCLUDED.last_rows, updated_at=now()"),
            {"o": oz_table, "f": fw_code, "q": sql_mssql, "n": res.get("vlozeno")})
        if repoint:
            s3.execute(_t("UPDATE fw.data_set SET db_connection_id=1, sql_text=:q WHERE id=:i"),
                       {"q": "SELECT * FROM tenant.%s" % oz_table, "i": src["dsid"]})
        s3.commit()
    finally:
        s3.close()
    return {"ok": True, "oz_table": oz_table, "fw_code": fw_code, "sloupcu": len(cols),
            "vlozeno": res.get("vlozeno"), "chyb": res.get("chyb"),
            "prvni_chyba": res.get("prvni_chyba"), "repoint": repoint,
            "cols": [c["name"] + " " + c["pg_type"] for c in cols]}


# ── Raw mirrory (bez fw.data_set) — cockpit-only zdroje s oz_* názvoslovím ──
# Marti 5.7.2026: dorovnání sady o výdejky/vydané poptávky/příjemky pro leader cockpit.
# resitel = COALESCE(LoginID z CisloZam, Autor) → řešitel všude. Auto-refresh přes
# oz_sync_all (uloženo v oz_mirror_def, sql_mssql). NErepointují žádný strom.
# Výdejky/příjemky omezené na 2023+ (fill() nestránkuje, plná historie by byla mega-pull).
_OZ_RAW_BASE = (
    "SELECT d.ID AS id, d.RadaDokladu AS rada, d.DruhPohybuZbo AS druh_pohybu, "
    "d.PoradoveCislo AS poradove_cislo, dbo.EC_GetDoklad(d.ID) AS doklad, "
    "RTRIM(d.CisloZakazky) AS cislozakazky, CAST(d.Splneno AS int) AS splneno, "
    "d.StredNaklad AS stredisko, d.CisloOrg AS cisloorg, org.Nazev AS nazev, "
    "orge._Zkratka_Nazvu AS zkratka_nazvu, COALESCE(z.LoginID, d.Autor) AS resitel, "
    "de._OznPrjZakaznik AS oznprjzakaznik, de._PopisPrjZakaznik AS popisprjzakaznik, "
    "dbo.EC_GetDoklad(d.NavaznyDoklad) AS navaznydoklad, d.NavaznaObjednavka AS navaznaobjednavka, "
    "d.Autor AS autor, CAST(d.SumaKcBezDPH AS numeric(19,2)) AS sumakcbezdph, d.DatPorizeni AS datporizeni "
    "FROM TabDokladyZbozi d WITH (NOLOCK) "
    "LEFT JOIN TabCisOrg org ON d.CisloOrg=org.CisloOrg "
    "LEFT JOIN TabCisOrg_EXT orge ON org.ID=orge.ID "
    "LEFT JOIN TabCisZam z ON d.CisloZam=z.Cislo "
    "LEFT JOIN TabDokladyZbozi_EXT de ON de.ID=d.ID "
    "WHERE %s"
)
# Vydané poptávky (řada 940): „neuzavřeno" = Realizovano=0 (ne Splneno), stejný vzor jako
# faktury ve vp_pipeline. Přemapujeme proto splneno→Realizovano jen pro tento raw mirror.
# (Marti 12.7.2026 „srovnej to"; splneno v cockpitu = generický 'closed' flag.)
_OZ_RAW_BASE_REALIZ = _OZ_RAW_BASE.replace(
    "CAST(d.Splneno AS int) AS splneno", "CAST(d.Realizovano AS int) AS splneno")

_OZ_RAW = {
    "oz_vy_popt": _OZ_RAW_BASE_REALIZ % "d.RadaDokladu='940'",
    "oz_vydejka": _OZ_RAW_BASE % ("d.RadaDokladu IN ('200','290') AND d.DruhPohybuZbo BETWEEN 2 AND 4 "
                                  "AND d.DatPorizeni >= '2023-01-01'"),
    "oz_prijemka": _OZ_RAW_BASE % "d.DruhPohybuZbo <= 1 AND d.DatPorizeni >= '2023-01-01'",
    # Úhrady (TabUhrady) — vazba na fakturu IDFak, částka, datum, původ platby. Základ pro
    # „co je zaplaceno" + pojistku proti dvojí platbě (saldo = faktura − úhrady). Marti 6.7.2026.
    # JEDNA tabulka, pole firma = company.id (EC=1, ES=2, ST=3). Multitenant/multifirma
    # (tenant≠firma; Marti 6.7.). ES cross-db [DB_IS], bez EC_GetDoklad (cross-db UDF padá).
    "oz_uhrady": (
        "SELECT u.ID AS id, 2 AS tenant_id, 1 AS firma, u.IDFak AS id_fak, dbo.EC_GetDoklad(u.IDFak) AS doklad_fak, "
        "u.Datum AS datum, u.CastkaUhrady AS castka_uhrady, u.Castka AS castka, "
        "u.CastkaPoBance AS castka_po_bance, u.Mena AS mena, u.Puvod AS puvod, "
        "u.RealUhradaVHM AS real_uhrada_hm "
        "FROM TabUhrady u WITH (NOLOCK) WHERE u.Datum >= '2024-01-01' "
        "UNION ALL "
        "SELECT u.ID AS id, 2 AS tenant_id, 2 AS firma, u.IDFak AS id_fak, CAST(NULL AS nvarchar(40)) AS doklad_fak, "
        "u.Datum AS datum, u.CastkaUhrady AS castka_uhrady, u.Castka AS castka, "
        "u.CastkaPoBance AS castka_po_bance, u.Mena AS mena, u.Puvod AS puvod, "
        "u.RealUhradaVHM AS real_uhrada_hm "
        "FROM [DB_IS].dbo.TabUhrady u WITH (NOLOCK) WHERE u.Datum >= '2024-01-01'"
    ),
    # PF k platbě (přijaté faktury) s PLNÝM filtrem návrhu k platbě — saldo + _FinZakaz +
    # _DnyPredPlatbou (per dodavatel) + SumaKcPoZao + Nehradit. Zdroj pro /platby-navrh. Marti 6.7.2026.
    "oz_pf_platba": (
        "SELECT d.ID AS id, 2 AS tenant_id, 1 AS firma, dbo.EC_GetDoklad(d.ID) AS doklad, d.PoradoveCislo AS poradove_cislo, "
        "d.RadaDokladu AS rada, d.DruhPohybuZbo AS druh, d.CisloOrg AS cislo_org, "
        "org.Nazev AS dodavatel, orge._Zkratka_Nazvu AS zkratka, d.DodFak AS var_symbol, "
        "ISNULL(NULLIF(LTRIM(RTRIM(d.Mena)),''),'CZK') AS mena, "
        # POZOR: Helios Saldo se ZÁMĚRNĚ NEzrcadlí (Marti 6.7. — smrtelně důležité). Saldo si
        # počítáme sami = suma_po_zao/suma_kc − naše úhrady (oz_uhrady), jinak by 10min refresh
        # přepsal naše saldo po vygenerování platáku. Zrcadlíme jen stabilní částky faktury.
        "CAST(d.SumaKc AS numeric(18,2)) AS suma_kc, CAST(d.SumaVal AS numeric(18,2)) AS suma_val, "
        "CAST(d.SumaKcPoZao AS numeric(18,2)) AS suma_po_zao, CAST(d.Realizovano AS int) AS realizovano, "
        "d.Obdobi AS obdobi, CONVERT(varchar(10), d.Splatnost, 23) AS splatnost, "
        "ISNULL(de._FinZakaz,0) AS fin_zakaz, ISNULL(de._NavrhPlatby,0) AS navrh_platby, "
        "ISNULL(de._FinSchvaleni,0) AS fin_schvaleni, ISNULL(orge._DnyPredPlatbou,5) AS dny_pred_platbou, "
        "ISNULL(d.Nehradit,0) AS nehradit, CONVERT(varchar(10), d.DatPorizeni, 23) AS dat_porizeni, "
        "d.PopisDodavky AS popis "
        "FROM TabDokladyZbozi d WITH (NOLOCK) "
        "LEFT JOIN TabCisOrg org ON d.CisloOrg=org.CisloOrg "
        "LEFT JOIN TabCisOrg_EXT orge ON org.ID=orge.ID "
        "LEFT JOIN TabDokladyZbozi_EXT de ON de.ID=d.ID "
        "WHERE d.DruhPohybuZbo BETWEEN 18 AND 19 AND d.PoradoveCislo>=0 "
        "AND d.DatPorizeni >= '2024-01-01'"  # scope dle DATA, ne dle Helios salda (to je naše)
    ),
    # Platáky (platební příkazy) — tuzemské (přehled Centrály 2370). Peťa si je kontroluje ("jsou to prachy").
    # Od 7.7.2026 platíme my → potřebujeme vlastní seznam zadaných platáku. RealizaceExport = vyexportováno.
    # Marti 7.7.2026: JEDEN zdroj = DB_EC. Firma se odvozuje z ES bankovního účtu
    # (TabBankSpojeni_EXT._RadaDokladuPoslCis=1 = ES účet, kam Helios ES zrcadlí mzdové
    # platáky; jinak EC). DB_EC je KOMPLETNÍ zdroj (ES platáky do 02.07.2026), dřívější
    # [DB_IS] větev byla dormantní (končila 09.06) → zahozena.
    "oz_platak_tuz": (
        "SELECT pt.ID AS id, 2 AS tenant_id, "
        "(CASE WHEN ISNULL(bse._RadaDokladuPoslCis,0)=1 THEN 2 ELSE 1 END) AS firma, "
        "pt.RealizaceExport AS realizace_export, "
        "CONVERT(varchar(10),pt.DatumVystaveni,23) AS datum_vystaveni, "
        "CONVERT(varchar(10),pt.DatumSplatnosti,23) AS datum_splatnosti, "
        "CONVERT(varchar(19),pt.DatPorizeni,120) AS dat_porizeni, "
        "bs.NazevBankSpoj AS odkud, "
        "CAST((SELECT COUNT(ID) FROM TabPlatTuzRDetail WHERE IDHlavaPP=pt.ID) AS int) AS pocet, "
        "CAST(pt.CastkaCelkem AS numeric(19,2)) AS castka_celkem, pt.Mena AS mena, "
        "pt.PocetExportu AS pocet_exportu, pt.TypPrikazu AS typ_prikazu, pt.Autor AS autor, "
        "CAST(bs.CisloUctu + '/' + bu.KodUstavu + ' ' + bs.Mena AS nvarchar(60)) AS odkud_cislo_uctu, "
        "pt.IDBankSpojeni AS id_bank_spojeni, pt.IdObdobi AS id_obdobi, "
        "CAST((SELECT STRING_AGG(CONVERT(nvarchar(20),r._PorCisFak),', ') FROM TabPlatTuzR o "
        "LEFT OUTER JOIN TabPlatTuzR_EXT r ON r.ID=o.ID WHERE o.IDHlavaPP=pt.ID) AS nvarchar(4000)) AS seznam_faktur, "
        "pte._PathPayFile AS path_pay_file "
        "FROM TabPlatTuz pt WITH (NOLOCK) "
        "LEFT OUTER JOIN TabPlatTuz_EXT pte ON pt.ID=pte.ID "
        "LEFT OUTER JOIN TabPenezniUstavy bu ON pt.IDBankUstavu=bu.ID "
        "LEFT OUTER JOIN TabBankSpojeni bs ON pt.IDBankSpojeni=bs.ID "
        "LEFT OUTER JOIN TabBankSpojeni_EXT bse ON bs.ID=bse.ID "
        "WHERE pt.TypPrikazu=0 AND YEAR(pt.DatPorizeni) IN (2025,2026)"
    ),
    # Platáky zahraniční (přehled Centrály 2375) — EUR, s IBAN/SWIFT příjemce.
    "oz_platak_zahr": (
        "SELECT pz.ID AS id, 2 AS tenant_id, "
        "(CASE WHEN ISNULL(plate._RadaDokladuPoslCis,0)=1 THEN 2 ELSE 1 END) AS firma, "
        "pz.RealizaceExport AS realizace_export, "
        "CONVERT(varchar(10),pz.DatumVystaveni,23) AS datum_vystaveni, "
        "CONVERT(varchar(10),pz.DatumSplatnosti,23) AS datum_splatnosti, "
        "CONVERT(varchar(19),pz.DatPorizeni,120) AS dat_porizeni, "
        "plat.NazevBankSpoj AS odkud, prij.NazevBankSpoj AS komu, "
        "pz.PocetDetailu AS pocet, CAST(pz.Castka AS numeric(19,2)) AS castka_celkem, pz.Mena AS mena, "
        "pz.IDCilovaZeme AS cilova_zeme, pz.Autor AS autor, pz.PopisPlatby1 AS popis, "
        "CAST(plat.CisloUctu + '/' + ubu.KodUstavu + ' ' + plat.Mena AS nvarchar(60)) AS odkud_cislo_uctu, "
        "CAST(prij.CisloUctu + '/' + pbu.KodUstavu AS nvarchar(60)) AS kam_cislo, prij.IBANPisemny AS kam_iban, pbu.SWIFTUstavu AS kam_swift, "
        "pz.Poplatky AS poplatky, pz.Priorita AS priorita, pz.IDObdobi AS id_obdobi, "
        "pz.IDBankSpojeniPlatce AS id_bank_spojeni, "
        "CAST((SELECT STRING_AGG(CONVERT(nvarchar(20),r._PorCisFak),', ') FROM TabPlatZahrDetail o "
        "LEFT OUTER JOIN TabPlatZahrDetail_EXT r ON r.ID=o.ID WHERE o.IDHlavaPPZ=pz.ID) AS nvarchar(4000)) AS seznam_faktur, "
        "pze._PathPayFile AS path_pay_file "
        "FROM TabPlatZahr pz WITH (NOLOCK) "
        "LEFT OUTER JOIN TabPlatZahr_EXT pze ON pz.ID=pze.ID "
        "LEFT OUTER JOIN TabPenezniUstavy ubu ON pz.IDBankUstavuPlatce=ubu.ID "
        "LEFT OUTER JOIN TabBankSpojeni plat ON pz.IDBankSpojeniPlatce=plat.ID "
        "LEFT OUTER JOIN TabBankSpojeni_EXT plate ON plat.ID=plate.ID "
        "LEFT OUTER JOIN TabPenezniUstavy pbu ON pz.IDBankUstavuPrijemce=pbu.ID "
        "LEFT OUTER JOIN TabBankSpojeni prij ON pz.IDBankSpojeniPrijemce=prij.ID "
        "WHERE YEAR(pz.DatPorizeni) IN (2025,2026)"
        # ES (System) nedělá zahraniční platby (0 zahr platáku) → jen firma=1 (EC). firma pole ale zůstává.
    ),
}


def mirror_raw(oz_table: str, tenant_id: int = 2):
    """Zrcadlí raw MSSQL dotaz z _OZ_RAW do tenant.<oz_table> + uloží do oz_mirror_def
    (auto-refresh přes sync_all). Nerepointuje žádný fw.data_set (cockpit-only zdroj)."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    sql_mssql = _OZ_RAW.get(oz_table)
    if not sql_mssql:
        return {"ok": False, "error": "neznámý oz_raw: %s (mám: %s)" % (oz_table, ", ".join(_OZ_RAW))}
    _ensure_def_table(tenant_id)
    cols = describe(sql_mssql)
    if not cols:
        return {"ok": False, "error": "sp_describe nevrátil sloupce"}
    create_table(oz_table, cols, tenant_id=tenant_id, drop=True)
    res = fill(oz_table, sql_mssql, cols, tenant_id=tenant_id)
    s = get_data_session()
    try:
        s.execute(_t(
            "INSERT INTO tenant.oz_mirror_def(oz_table,fw_code,sql_mssql,last_sync_at,last_rows) "
            "VALUES(:o,:f,:q,now(),:n) ON CONFLICT (oz_table) DO UPDATE SET "
            "fw_code=EXCLUDED.fw_code, sql_mssql=EXCLUDED.sql_mssql, last_sync_at=now(), "
            "last_rows=EXCLUDED.last_rows, updated_at=now()"),
            {"o": oz_table, "f": "raw", "q": sql_mssql, "n": res.get("vlozeno")})
        s.commit()
    finally:
        s.close()
    return {"ok": True, "oz_table": oz_table, "sloupcu": len(cols), "vlozeno": res.get("vlozeno"),
            "chyb": res.get("chyb"), "prvni_chyba": res.get("prvni_chyba")}


def mirror_raw_all(tenant_id: int = 2):
    """Vytvoří všechna raw zrcadla (oz_vy_popt, oz_vydejka, oz_prijemka)."""
    out = []
    for t in _OZ_RAW:
        try:
            out.append({"oz": t, **mirror_raw(t, tenant_id=tenant_id)})
        except Exception as e:  # noqa: BLE001
            out.append({"oz": t, "ok": False, "error": str(e)[:200]})
    return {"ok": True, "vysledky": out}


# Plán zrcadel: (fw.data_source code, cílová PG tabulka). Zkratky Marti 2.7.:
# prij_ = přijaté, vy_ = vydané, fa = faktury.
_OZ_PLAN = [
    ("vp_zakazky", "oz_zakazky"),
    ("vp_poptavky", "oz_prij_popt"),
    ("vp_kalkulace", "oz_vy_nab"),
    ("vp_prijate_obj", "oz_prij_obj"),
    ("vp_kalk_nakup", "oz_kalkulace"),
    ("vp_vydane_obj", "oz_vy_obj"),
    ("fin_prijate_faktury", "oz_prij_fa"),
    ("fin_vydane_faktury", "oz_vy_fa"),
    ("nakup_prij_nab", "oz_prij_nab"),
]


def mirror_all(tenant_id: int = 2, plan=None):
    """Sekvenčně zrcadlí všechny přehledy z plánu (jeden po druhém — MCP rate limit)."""
    res = []
    for fw, tbl in (plan or _OZ_PLAN):
        try:
            r = mirror(fw, tbl, tenant_id=tenant_id)
            res.append({"oz": tbl, "ok": r.get("ok"), "vlozeno": r.get("vlozeno"),
                        "chyb": r.get("chyb"), "err": r.get("error") or r.get("prvni_chyba")})
        except Exception as e:  # noqa: BLE001
            res.append({"oz": tbl, "ok": False, "err": str(e)[:200]})
    return {"ok": True, "vysledky": res}


def sync_all(tenant_id: int = 2):
    """Obnoví data ve všech zrcadlech z uložených MSSQL dotazů (scheduled refresh)."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        tbls = [r[0] for r in s.execute(_t("SELECT oz_table FROM tenant.oz_mirror_def ORDER BY oz_table"))]
    finally:
        s.close()
    res = []
    for t in tbls:
        try:
            r = sync(t, tenant_id=tenant_id)
            res.append({"oz": t, "vlozeno": r.get("vlozeno"), "chyb": r.get("chyb"), "err": r.get("error")})
        except Exception as e:  # noqa: BLE001
            res.append({"oz": t, "err": str(e)[:200]})
    celkem = sum(int(x.get("vlozeno") or 0) for x in res)
    chyby = sum(1 for x in res if x.get("err"))
    return {"ok": chyby == 0, "celkem": celkem, "tabulek": len(res), "chyb": chyby, "vysledky": res}


def rename(old_oz: str, new_oz: str, tenant_id: int = 2):
    """Přejmenuje mirror tabulku (běží jako strategie=owner): ALTER + oz_mirror_def + repoint data_set."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        s.execute(_t("ALTER TABLE tenant.%s RENAME TO %s" % (old_oz, new_oz)))
        s.execute(_t('GRANT ALL ON tenant.%s TO strategie, "Marti-AI"' % new_oz))
        s.execute(_t("UPDATE tenant.oz_mirror_def SET oz_table=:n, updated_at=now() WHERE oz_table=:o"),
                  {"n": new_oz, "o": old_oz})
        s.execute(_t("UPDATE fw.data_set SET sql_text=:q WHERE sql_text=:old"),
                  {"q": "SELECT * FROM tenant.%s" % new_oz, "old": "SELECT * FROM tenant.%s" % old_oz})
        s.commit()
        return {"ok": True, "old": old_oz, "new": new_oz}
    finally:
        s.close()


def sync(oz_table: str, tenant_id: int = 2):
    """Obnoví data v tenant.<oz_table> z uloženého MSSQL dotazu (pro scheduled refresh)."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session
    s = get_data_session()
    try:
        d = s.execute(_t("SELECT fw_code, sql_mssql FROM tenant.oz_mirror_def WHERE oz_table=:o"),
                      {"o": oz_table}).mappings().first()
    finally:
        s.close()
    if not d:
        return {"ok": False, "error": "oz_mirror_def pro %s neexistuje" % oz_table}
    cols = describe(d["sql_mssql"])
    res = fill(oz_table, d["sql_mssql"], cols, tenant_id=tenant_id)
    s2 = get_data_session()
    try:
        s2.execute(_t("UPDATE tenant.oz_mirror_def SET last_sync_at=now(), last_rows=:n WHERE oz_table=:o"),
                   {"n": res.get("vlozeno"), "o": oz_table})
        s2.commit()
    finally:
        s2.close()
    return {"ok": True, "oz_table": oz_table, "vlozeno": res.get("vlozeno"), "chyb": res.get("chyb")}
