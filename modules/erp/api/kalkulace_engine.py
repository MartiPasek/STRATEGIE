"""
Kalkulační engine — oprášení systému z DB_EC (2014) do PG + výpočet.

Marti 1.7.2026: v roce 2014 postavil v DB_EC kompletní datový model kalkulace
rozváděčů, kterému "nikdo nevdechl život". Struktura je ověřená → zrcadlíme ji
do PG (tenant.kalk_*), data z 2014 jako baseline (zdroj='ec2014') k pozdějšímu
refreshi z aktuálních STANDARD kalkulací. Detail: docs/Kalkulacni_engine_DB_EC_2014.md.

Princip (per zákazník!): STANDARD = per CisloOrg jiná sestava skupin + jiné rabaty.
Cenový řetězec: CC (ceníková) × prodejní rabat = prodejní cena; × nákupní rabat = NC.
VKM = K_VKM × báze_VKM × koef; Arbeit = K_ARB × báze_Arbeit × koef.

@@ příkazy (dispatch v router.diag_sql):
  @@KALKSYNC            → zrcadlí EC_Kalk* (DB_EC přes MCP) → tenant.kalk_* (baseline)
  @@KALKINFO            → přehled naplnění zrcadla (počty per tabulka)
"""
from __future__ import annotations

import json


def _mcp():
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    return get_eurosoft_mcp_client()


def _ec(sql: str) -> list[dict]:
    """DB_EC SELECT přes MCP → list dictů."""
    mcp = _mcp()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP klient není dostupný")
    raw = mcp.call_tool_sync(full_name="eurosoft_strategie_query_raw",
                             arguments={"sql": sql, "db_name": "DB_EC"},
                             conversation_id=None)
    res = json.loads(raw)
    if not res.get("ok"):
        raise RuntimeError("MCP EC dotaz selhal: %s" % (res.get("message") or res.get("error")))
    return res.get("rows") or []


def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except Exception:
        return None


def _int(v):
    if v in (None, ""):
        return None
    try:
        return int(v)
    except Exception:
        return None


def _bool(v):
    if v in (None, ""):
        return None
    return bool(int(v)) if str(v).strip() in ("0", "1") else bool(v)


def sync_engine() -> dict:
    """Full refresh zrcadla tenant.kalk_* z DB_EC (baseline zdroj='ec2014')."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    out: dict = {"ok": True}
    sd = get_data_session()
    try:
        # 1) KMEN (identita dílů použitých v kalk tabulkách)
        kmen = _ec(
            "SELECT Z.ID, Z.RegCis, Z.Nazev1, Z.SKP FROM TabKmenZbozi Z WHERE Z.ID IN ("
            " SELECT IDKmenZbozi FROM EC_KalkKoeficienty"
            " UNION SELECT IDKmenZbozi FROM EC_KalkCena"
            " UNION SELECT IDKmenZbozi FROM EC_KalkRabaty"
            " UNION SELECT IDKmenZbozi FROM EC_KalkSkupinyPolozky)")
        sd.execute(_t("DELETE FROM tenant.kalk_kmen WHERE zdroj='ec2014'"))
        for r in kmen:
            sd.execute(_t(
                "INSERT INTO tenant.kalk_kmen (kmen_ec_id,reg_cis,nazev,skp) "
                "VALUES (:i,:r,:n,:s) ON CONFLICT (kmen_ec_id) DO UPDATE SET "
                "reg_cis=EXCLUDED.reg_cis,nazev=EXCLUDED.nazev,skp=EXCLUDED.skp,synced_at=now()"),
                {"i": _int(r.get("ID")), "r": r.get("RegCis"), "n": r.get("Nazev1"), "s": r.get("SKP")})
        out["kmen"] = len(kmen)

        # 2) KOEFICIENTY (K_VKM + K_ARB per díl)
        koef = _ec("SELECT ID,IDKmenZbozi,K_VKM,K_ARB,Puvod,Poznamka FROM EC_KalkKoeficienty")
        sd.execute(_t("DELETE FROM tenant.kalk_koef WHERE zdroj='ec2014'"))
        for r in koef:
            sd.execute(_t(
                "INSERT INTO tenant.kalk_koef (ec_id,kmen_ec_id,k_vkm,k_arb,puvod,poznamka) "
                "VALUES (:e,:k,:v,:a,:p,:z)"),
                {"e": _int(r.get("ID")), "k": _int(r.get("IDKmenZbozi")),
                 "v": _num(r.get("K_VKM")), "a": _num(r.get("K_ARB")),
                 "p": r.get("Puvod"), "z": r.get("Poznamka")})
        out["koef"] = len(koef)

        # 3) CENY (CC ceníková)
        cena = _ec("SELECT ID,IDKmenZbozi,KalkCena,Mena,Poznamka,Blokovano,"
                   "CONVERT(varchar(19),DatZmeny,120) AS DatZmeny FROM EC_KalkCena")
        sd.execute(_t("DELETE FROM tenant.kalk_cena WHERE zdroj='ec2014'"))
        for r in cena:
            sd.execute(_t(
                "INSERT INTO tenant.kalk_cena (ec_id,kmen_ec_id,cc_cena,mena,poznamka,blokovano,dat_zmeny) "
                "VALUES (:e,:k,:c,:m,:p,:b,:d)"),
                {"e": _int(r.get("ID")), "k": _int(r.get("IDKmenZbozi")),
                 "c": _num(r.get("KalkCena")), "m": r.get("Mena"), "p": r.get("Poznamka"),
                 "b": _bool(r.get("Blokovano")), "d": r.get("DatZmeny") or None})
        out["cena"] = len(cena)

        # 4) RABATY (Prodejní + Nákupní, per díl a per CisloOrg/dodavatel)
        rab = _ec("SELECT ID,IDKmenZbozi,TypText,Rabat,CisloOrg,CisloOrgDod,Poznamka FROM EC_KalkRabaty")
        sd.execute(_t("DELETE FROM tenant.kalk_rabat WHERE zdroj='ec2014'"))
        for r in rab:
            sd.execute(_t(
                "INSERT INTO tenant.kalk_rabat (ec_id,kmen_ec_id,typ_text,rabat,cislo_org,cislo_org_dod,poznamka) "
                "VALUES (:e,:k,:t,:r,:o,:d,:p)"),
                {"e": _int(r.get("ID")), "k": _int(r.get("IDKmenZbozi")), "t": r.get("TypText"),
                 "r": _num(r.get("Rabat")), "o": _int(r.get("CisloOrg")),
                 "d": _int(r.get("CisloOrgDod")), "p": r.get("Poznamka")})
        out["rabat"] = len(rab)

        # 5) STANDARD SKUPINY
        sk = _ec("SELECT ID,Cislo,Nazev,Poradi,Zamceno FROM EC_KalkSkupiny")
        sd.execute(_t("DELETE FROM tenant.kalk_skupina WHERE zdroj='ec2014'"))
        for r in sk:
            sd.execute(_t(
                "INSERT INTO tenant.kalk_skupina (ec_id,cislo,nazev,poradi,zamceno) "
                "VALUES (:e,:c,:n,:p,:z)"),
                {"e": _int(r.get("ID")), "c": _int(r.get("Cislo")), "n": r.get("Nazev"),
                 "p": _int(r.get("Poradi")), "z": _bool(r.get("Zamceno"))})
        out["skupina"] = len(sk)

        # 6) STANDARD POLOŽKY SKUPIN
        skp = _ec("SELECT ID,ID_Skupina,IDKmenZbozi,Poradi FROM EC_KalkSkupinyPolozky")
        sd.execute(_t("DELETE FROM tenant.kalk_skupina_pol WHERE zdroj='ec2014'"))
        for r in skp:
            sd.execute(_t(
                "INSERT INTO tenant.kalk_skupina_pol (ec_id,skupina_ec_id,kmen_ec_id,poradi) "
                "VALUES (:e,:s,:k,:p)"),
                {"e": _int(r.get("ID")), "s": _int(r.get("ID_Skupina")),
                 "k": _int(r.get("IDKmenZbozi")), "p": _int(r.get("Poradi"))})
        out["skupina_pol"] = len(skp)

        # 7) SESTAVY (per CisloOrg = per zákazník)
        se = _ec("SELECT ID,CisloOrg,Nazev,StatusText,Poznamka FROM EC_KalkSestavySkup")
        sd.execute(_t("DELETE FROM tenant.kalk_sestava WHERE zdroj='ec2014'"))
        for r in se:
            sd.execute(_t(
                "INSERT INTO tenant.kalk_sestava (ec_id,cislo_org,nazev,status_text,poznamka) "
                "VALUES (:e,:o,:n,:s,:p)"),
                {"e": _int(r.get("ID")), "o": _int(r.get("CisloOrg")), "n": r.get("Nazev"),
                 "s": r.get("StatusText"), "p": r.get("Poznamka")})
        out["sestava"] = len(se)

        # 8) SESTAVY — POLOŽKY (které skupiny na kterém listu)
        sep = _ec("SELECT ID,IDHlav,ID_List,PoradiListu,ID_Skupiny,Poradi,Aktivni FROM EC_KalkSestavySkupPolozky")
        sd.execute(_t("DELETE FROM tenant.kalk_sestava_pol WHERE zdroj='ec2014'"))
        for r in sep:
            sd.execute(_t(
                "INSERT INTO tenant.kalk_sestava_pol (ec_id,sestava_ec_id,id_list,poradi_listu,skupina_ec_id,poradi,aktivni) "
                "VALUES (:e,:h,:l,:pl,:s,:p,:a)"),
                {"e": _int(r.get("ID")), "h": _int(r.get("IDHlav")), "l": _int(r.get("ID_List")),
                 "pl": _int(r.get("PoradiListu")), "s": _int(r.get("ID_Skupiny")),
                 "p": _int(r.get("Poradi")), "a": _bool(r.get("Aktivni"))})
        out["sestava_pol"] = len(sep)

        sd.commit()
    finally:
        sd.close()
    return out


def engine_info() -> dict:
    """Přehled naplnění zrcadla."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    sd = get_data_session()
    try:
        q = {}
        for tab in ("kalk_kmen", "kalk_koef", "kalk_cena", "kalk_rabat",
                    "kalk_skupina", "kalk_skupina_pol", "kalk_sestava", "kalk_sestava_pol"):
            q[tab] = sd.execute(_t("SELECT COUNT(*) FROM tenant.%s" % tab)).scalar()
        q["cena_prodejni_rabat_dilu"] = sd.execute(_t(
            "SELECT COUNT(DISTINCT kmen_ec_id) FROM tenant.kalk_rabat WHERE typ_text='Prodejní'")).scalar()
        return {"ok": True, "pocty": q}
    finally:
        sd.close()
