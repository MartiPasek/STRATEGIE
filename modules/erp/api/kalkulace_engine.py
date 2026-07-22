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


def refresh_std(zdroj: str = "std2026") -> dict:
    """Merge tenant.kalk_std_stage (naplněná z aktuální STANDARD kalkulace) → kalk_cena/rabat/koef.
    Match na existující díl přes normalizované obj. číslo; nenalezené díly = nové (negativní kmen_ec_id).
    Data dostanou tag `zdroj` (std2026) = přebíjí baseline ec2014 v enginu."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    sd = get_data_session()
    out = {"ok": True, "zdroj": zdroj}
    # inline resolver kmen z obj. čísla (normalizovaně, prefer kratší = STANDARD díl)
    MS = ("(SELECT k.kmen_ec_id FROM tenant.kalk_kmen k WHERE "
          "replace(replace(upper(k.reg_cis),' ',''),'-','') LIKE '%'||s.objn||'%' "
          "ORDER BY length(k.reg_cis) LIMIT 1)")
    try:
        # 1) nové díly (bez shody) → nový kmen s negativním id
        out["nove_dily"] = sd.execute(_t(
            "INSERT INTO tenant.kalk_kmen (kmen_ec_id, reg_cis, nazev, zdroj) "
            "SELECT (SELECT COALESCE(MIN(kmen_ec_id),0) FROM tenant.kalk_kmen) - row_number() OVER (ORDER BY s.objn), "
            "s.obj, s.nazev, :z FROM tenant.kalk_std_stage s WHERE " + MS + " IS NULL RETURNING 1"),
            {"z": zdroj}).rowcount
        # 2) purge předchozí std pro dotčené díly
        for tab in ("kalk_cena", "kalk_rabat", "kalk_koef"):
            sd.execute(_t("DELETE FROM tenant." + tab + " WHERE zdroj=:z AND kmen_ec_id IN "
                          "(SELECT " + MS + " FROM tenant.kalk_std_stage s)"), {"z": zdroj})
        # 3) insert čerstvá data (negativní ec_id pod stávající minimum), kmen resolve inline
        out["cena"] = sd.execute(_t(
            "INSERT INTO tenant.kalk_cena (ec_id,kmen_ec_id,cc_cena,mena,zdroj) "
            "SELECT (SELECT COALESCE(MIN(ec_id),0) FROM tenant.kalk_cena) - row_number() OVER (ORDER BY s.objn), "
            + MS + ", s.cc, 'EUR', :z FROM tenant.kalk_std_stage s WHERE s.cc IS NOT NULL AND " + MS + " IS NOT NULL RETURNING 1"),
            {"z": zdroj}).rowcount
        out["rabat"] = sd.execute(_t(
            "INSERT INTO tenant.kalk_rabat (ec_id,kmen_ec_id,typ_text,rabat,zdroj) "
            "SELECT (SELECT COALESCE(MIN(ec_id),0) FROM tenant.kalk_rabat) - row_number() OVER (ORDER BY s.objn), "
            + MS + ", 'Prodejní', s.rabat, :z FROM tenant.kalk_std_stage s WHERE s.rabat IS NOT NULL AND " + MS + " IS NOT NULL RETURNING 1"),
            {"z": zdroj}).rowcount
        out["koef"] = sd.execute(_t(
            "INSERT INTO tenant.kalk_koef (ec_id,kmen_ec_id,k_vkm,k_arb,puvod,zdroj) "
            "SELECT (SELECT COALESCE(MIN(ec_id),0) FROM tenant.kalk_koef) - row_number() OVER (ORDER BY s.objn), "
            + MS + ", s.koef, s.koef, :z, :z FROM tenant.kalk_std_stage s WHERE s.koef IS NOT NULL AND " + MS + " IS NOT NULL RETURNING 1"),
            {"z": zdroj}).rowcount
        sd.commit()
    finally:
        sd.close()
    return out


def dily_search(q: str = "", limit: int = 300) -> dict:
    """Katalog dílů: kmen + nejlepší CC/rabat/koef (priorita std) + zdroj. Filtr q na reg_cis/nazev."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    sd = get_data_session()
    try:
        where = ""
        params = {"lim": min(int(limit or 300), 1000)}
        if q:
            where = ("WHERE replace(replace(upper(k.reg_cis),' ',''),'-','') LIKE :q "
                     "OR upper(k.nazev) LIKE :qn")
            import re
            params["q"] = "%" + re.sub(r"[^0-9A-Za-z]", "", q).upper() + "%"
            params["qn"] = "%" + q.upper() + "%"
        rows = sd.execute(_t(
            "SELECT k.kmen_ec_id, k.reg_cis, k.nazev, "
            "(SELECT c.cc_cena FROM tenant.kalk_cena c WHERE c.kmen_ec_id=k.kmen_ec_id "
            "  ORDER BY " + _SRC_PRIO + ", c.ec_id DESC LIMIT 1) cc, "
            "(SELECT c.zdroj FROM tenant.kalk_cena c WHERE c.kmen_ec_id=k.kmen_ec_id "
            "  ORDER BY " + _SRC_PRIO + ", c.ec_id DESC LIMIT 1) cc_zdroj, "
            "(SELECT r.rabat FROM tenant.kalk_rabat r WHERE r.kmen_ec_id=k.kmen_ec_id AND r.typ_text='Prodejní' "
            "  ORDER BY " + _SRC_PRIO + ", r.ec_id DESC LIMIT 1) rabat, "
            "(SELECT o.k_vkm FROM tenant.kalk_koef o WHERE o.kmen_ec_id=k.kmen_ec_id "
            "  ORDER BY " + _SRC_PRIO + ", o.ec_id DESC LIMIT 1) k_vkm, "
            "(SELECT o.k_arb FROM tenant.kalk_koef o WHERE o.kmen_ec_id=k.kmen_ec_id "
            "  ORDER BY " + _SRC_PRIO + ", o.ec_id DESC LIMIT 1) k_arb "
            "FROM tenant.kalk_kmen k " + where + " ORDER BY k.reg_cis LIMIT :lim"), params)
        out = []
        for r in rows:
            m = dict(r._mapping)
            for f in ("cc", "rabat", "k_vkm", "k_arb"):
                if m.get(f) is not None:
                    m[f] = float(m[f])
            m["prodejni"] = round(m["cc"] * (1 + (m.get("rabat") or 0) / 100.0), 2) if m.get("cc") is not None else None
            out.append(m)
        return {"ok": True, "dily": out}
    finally:
        sd.close()


def standard_groups() -> dict:
    """STANDARD skupiny (v pořadí) + počet položek."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    sd = get_data_session()
    try:
        rows = sd.execute(_t(
            "SELECT s.ec_id, s.cislo, s.nazev, s.poradi, "
            "(SELECT COUNT(*) FROM tenant.kalk_skupina_pol p WHERE p.skupina_ec_id=s.ec_id) pocet "
            "FROM tenant.kalk_skupina s ORDER BY s.poradi, s.cislo"))
        return {"ok": True, "skupiny": [dict(r._mapping) for r in rows]}
    finally:
        sd.close()


def standard_items(skupina_ec_id: int) -> dict:
    """Položky STANDARD skupiny + nejlepší CC/rabat/koef."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    sd = get_data_session()
    try:
        rows = sd.execute(_t(
            "SELECT p.poradi, k.kmen_ec_id, k.reg_cis, k.nazev, "
            "(SELECT c.cc_cena FROM tenant.kalk_cena c WHERE c.kmen_ec_id=k.kmen_ec_id ORDER BY " + _SRC_PRIO + ", c.ec_id DESC LIMIT 1) cc, "
            "(SELECT r.rabat FROM tenant.kalk_rabat r WHERE r.kmen_ec_id=k.kmen_ec_id AND r.typ_text='Prodejní' ORDER BY " + _SRC_PRIO + ", r.ec_id DESC LIMIT 1) rabat, "
            "(SELECT o.k_arb FROM tenant.kalk_koef o WHERE o.kmen_ec_id=k.kmen_ec_id ORDER BY " + _SRC_PRIO + ", o.ec_id DESC LIMIT 1) koef "
            "FROM tenant.kalk_skupina_pol p JOIN tenant.kalk_kmen k ON k.kmen_ec_id=p.kmen_ec_id "
            "WHERE p.skupina_ec_id=:s ORDER BY p.poradi"), {"s": int(skupina_ec_id)})
        out = []
        for r in rows:
            m = dict(r._mapping)
            for f in ("cc", "rabat", "koef"):
                if m.get(f) is not None:
                    m[f] = float(m[f])
            out.append(m)
        return {"ok": True, "polozky": out}
    finally:
        sd.close()


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
        q["zdroje_cena"] = [dict(r._mapping) for r in sd.execute(_t(
            "SELECT zdroj, COUNT(*) n FROM tenant.kalk_cena GROUP BY zdroj ORDER BY zdroj"))]
        return {"ok": True, "pocty": q}
    finally:
        sd.close()


# ── VÝPOČTOVÝ ENGINE ───────────────────────────────────────────────────
# Priorita zdroje dat: aktuální STANDARD (std*) přebíjí baseline 2014 (ec2014).
_SRC_PRIO = "CASE WHEN zdroj LIKE 'std%' THEN 0 ELSE 1 END"


def _norm(s: str) -> str:
    import re
    return re.sub(r"[^0-9A-Za-z]", "", (s or "")).upper()


def _resolve_item(sd, reg_cis: str, cislo_org=None) -> dict:
    """Najde díl v zrcadle podle obj. čísla (normalizovaně) + vytáhne CC, rabat, koef.
    Priorita: aktuální STANDARD před 2014; rabat preferuje per-zákazník (cislo_org)."""
    from sqlalchemy import text as _t
    nrm = _norm(reg_cis)
    if not nrm:
        return {"found": False}
    # díl (kmen) — nejlepší shoda na normalizované reg_cis (obsahuje, kvůli prefixu výrobce)
    km = sd.execute(_t(
        "SELECT kmen_ec_id, reg_cis, nazev FROM tenant.kalk_kmen "
        "WHERE replace(replace(upper(reg_cis),' ',''),'-','') LIKE :p "
        "ORDER BY length(reg_cis) LIMIT 1"), {"p": "%" + nrm + "%"}).first()
    if not km:
        return {"found": False, "reg_cis": reg_cis}
    kid = km.kmen_ec_id
    cc = sd.execute(_t(
        "SELECT cc_cena, mena, zdroj FROM tenant.kalk_cena WHERE kmen_ec_id=:k "
        "ORDER BY " + _SRC_PRIO + ", ec_id DESC LIMIT 1"), {"k": kid}).first()
    rp = sd.execute(_t(
        "SELECT rabat, cislo_org, zdroj FROM tenant.kalk_rabat WHERE kmen_ec_id=:k AND typ_text='Prodejní' "
        "ORDER BY CASE WHEN cislo_org=:o THEN 0 WHEN cislo_org IS NULL THEN 1 ELSE 2 END, " + _SRC_PRIO +
        ", ec_id DESC LIMIT 1"), {"k": kid, "o": cislo_org}).first()
    ko = sd.execute(_t(
        "SELECT k_vkm, k_arb, zdroj FROM tenant.kalk_koef WHERE kmen_ec_id=:k "
        "ORDER BY " + _SRC_PRIO + ", ec_id DESC LIMIT 1"), {"k": kid}).first()
    return {
        "found": True, "kmen_ec_id": kid, "reg_cis": km.reg_cis, "nazev": km.nazev,
        "cc": float(cc.cc_cena) if cc and cc.cc_cena is not None else None,
        "mena": cc.mena if cc else None, "cc_zdroj": cc.zdroj if cc else None,
        "rabat_prod": float(rp.rabat) if rp and rp.rabat is not None else None,
        "rabat_zdroj": rp.zdroj if rp else None,
        "k_vkm": float(ko.k_vkm) if ko and ko.k_vkm is not None else None,
        "k_arb": float(ko.k_arb) if ko and ko.k_arb is not None else None,
        "koef_zdroj": ko.zdroj if ko else None,
    }


def compute(bom: list, cislo_org=None, base_vkm: float = 14.5, base_arb: float = 28.0,
            koef_g: float = 1.0, marze_pct: float = 0.0) -> dict:
    """Spočítá kalkulaci nad zrcadlem. bom = [{'reg_cis','qty'} …].
    Řádek: prodejní = CC×(1+rabat/100); VKM = k_vkm×base_vkm×koef_g;
    Arbeit = k_arb×base_arb×koef_g; hodiny = qty×k_arb; řádek = (prodejní+VKM+Arbeit)×qty."""
    from core.database_data import get_data_session
    sd = get_data_session()
    lines = []
    try:
        for it in bom:
            reg = str(it.get("reg_cis") or "").strip()
            qty = float(it.get("qty") or 0)
            r = _resolve_item(sd, reg, cislo_org)
            miss = []
            if not r.get("found"):
                lines.append({"reg_cis": reg, "qty": qty, "found": False, "missing": ["nenalezen"]})
                continue
            cc = r.get("cc"); rab = r.get("rabat_prod"); kv = r.get("k_vkm"); ka = r.get("k_arb")
            if cc is None:
                miss.append("cena")
            if kv is None:
                miss.append("koef")
            prodejni = round(cc * (1 + (rab or 0) / 100.0), 2) if cc is not None else None
            vkm = round((kv or 0) * base_vkm * koef_g, 2)
            arb = round((ka or 0) * base_arb * koef_g, 2)
            hod = round(qty * (ka or 0), 2)
            radek = round(((prodejni or 0) + vkm + arb) * qty, 2)
            lines.append({
                "reg_cis": r["reg_cis"], "nazev": r["nazev"], "qty": qty,
                "cc": cc, "rabat_prod": rab, "prodejni": prodejni,
                "k_vkm": kv, "k_arb": ka, "vkm": vkm, "arbeit": arb,
                "hodiny": hod, "radek": radek,
                "zdroj": {"cena": r.get("cc_zdroj"), "rabat": r.get("rabat_zdroj"), "koef": r.get("koef_zdroj")},
                "missing": miss,
            })
    finally:
        sd.close()
    mat = round(sum((l.get("prodejni") or 0) * l["qty"] for l in lines if l.get("found", True)), 2)
    vkm_t = round(sum(l.get("vkm", 0) for l in lines), 2)
    arb_t = round(sum(l.get("arbeit", 0) for l in lines), 2)
    hod_t = round(sum(l.get("hodiny", 0) for l in lines), 2)
    radek_t = round(sum(l.get("radek", 0) for l in lines), 2)
    marze = round(radek_t * marze_pct / 100.0, 2)
    return {
        "ok": True, "cislo_org": cislo_org,
        "baze": {"vkm": base_vkm, "arbeit": base_arb, "koef": koef_g, "marze_pct": marze_pct},
        "souhrn": {"material": mat, "vkm": vkm_t, "arbeit": arb_t, "hodiny": hod_t,
                   "radky_celkem": radek_t, "marze": marze, "celkem_s_marzi": round(radek_t + marze, 2),
                   "polozek": len(lines), "chybi_cena": sum(1 for l in lines if "cena" in l.get("missing", [])),
                   "chybi_koef": sum(1 for l in lines if "koef" in l.get("missing", [])),
                   "nenalezeno": sum(1 for l in lines if not l.get("found", True))},
        "radky": lines,
    }


def compute_from_cmd(rest: str) -> dict:
    """@@KALKCALC org=NN vkm=14.5 arb=28 | REGCIS*QTY, REGCIS*QTY, …"""
    cislo_org = None; bvkm = 14.5; barb = 28.0; kg = 1.0; mar = 0.0
    head, _, body = rest.partition("|")
    for tok in head.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            try:
                if k == "org":
                    cislo_org = int(v)
                elif k in ("vkm", "base_vkm"):
                    bvkm = float(v)
                elif k in ("arb", "arbeit"):
                    barb = float(v)
                elif k == "koef":
                    kg = float(v)
                elif k in ("marze", "marze_pct"):
                    mar = float(v)
            except Exception:
                pass
    bom = []
    for part in body.split(","):
        part = part.strip()
        if not part:
            continue
        if "*" in part:
            reg, q = part.rsplit("*", 1)
        else:
            reg, q = part, "1"
        try:
            qn = float(q)
        except Exception:
            qn = 1.0
        bom.append({"reg_cis": reg.strip(), "qty": qn})
    res = compute(bom, cislo_org, bvkm, barb, kg, mar)
    # bridge-friendly: rows tabulka (řádky + součet)
    rows = []
    for l in res["radky"]:
        rows.append({
            "reg_cis": l.get("reg_cis"), "nazev": (l.get("nazev") or "")[:26], "ks": l.get("qty"),
            "CC": l.get("cc"), "rabat": l.get("rabat_prod"), "cena": l.get("prodejni"),
            "VKM": l.get("vkm"), "Arbeit": l.get("arbeit"), "hod": l.get("hodiny"),
            "radek": l.get("radek"), "chybi": ",".join(l.get("missing", [])) or "-",
        })
    s = res["souhrn"]
    rows.append({"reg_cis": "== SOUČET ==", "nazev": "%d pol." % s["polozek"], "ks": None,
                 "CC": None, "rabat": None, "cena": s["material"], "VKM": s["vkm"],
                 "Arbeit": s["arbeit"], "hod": s["hodiny"], "radek": s["radky_celkem"],
                 "chybi": "cena:%d koef:%d nenal:%d" % (s["chybi_cena"], s["chybi_koef"], s["nenalezeno"])})
    res["rows"] = rows
    return res


# ── Produkční profily ABSAUGWERK (Claude C23, 18.7.2026) ──────────────────────
# Z reálných kalkulací: EK262940 (FLEX+) + EK263380 SMART NASS. cislo_org=10077.
PROFILY = {
    "flex": {
        "nazev": "ABSAUGWERK · FLEX+ Schaltschrank",
        "cislo_org": 10077, "vkm": 14.5, "arb": 28.0, "marze": 12.0,
        "projekt": 180.0, "revize": 90.0, "transport": 60.0, "floor": {},
    },
    "nass": {
        "nazev": "ABSAUGWERK · SMART NASS Steuerung",
        "cislo_org": 10077, "vkm": 11.0, "arb": 28.0, "marze": 8.0,
        "projekt": 0.0, "revize": 0.0, "transport": 0.0,
        "floor": {"1.1": 1170, "2.2": 1170, "3.0": 1170, "4.0": 1200, "5.5": 1300,
                  "7.5": 1320, "11": 1500, "15": 1550, "18.5": 1700, "22": 1800},
    },
}


def compute_profile(bom, profil_kod, kw=None):
    """Produkční kalkulace přes pojmenovaný profil (sazby+marže+floor+přirážky)."""
    p = PROFILY.get((profil_kod or "").lower())
    if not p:
        return {"ok": False, "error": "neznámý profil '%s' (známé: %s)" % (profil_kod, ", ".join(PROFILY))}
    res = compute(bom, p.get("cislo_org"), p["vkm"], p["arb"], 1.0, p["marze"])
    s = res["souhrn"]
    fixni = p["projekt"] + p["revize"] + p["transport"]
    gesamt = round(s["celkem_s_marzi"] + fixni, 2)
    floor = p.get("floor", {}).get(str(kw)) if kw is not None else None
    floor_hit = bool(floor and gesamt < floor)
    if floor_hit:
        gesamt = float(floor)
    res["profil"] = {"kod": profil_kod, "nazev": p["nazev"], "vkm": p["vkm"], "arb": p["arb"],
                     "marze": p["marze"], "projekt": p["projekt"], "revize": p["revize"],
                     "transport": p["transport"], "floor": floor, "floor_hit": floor_hit}
    res["gesamt"] = gesamt
    res["nabidnout"] = round(gesamt / 10.0) * 10
    rows = res.get("rows") or []
    rows.append({"reg_cis": "== GESAMT ==", "nazev": p["nazev"][:26], "ks": None,
                 "CC": None, "rabat": None, "cena": s["material"], "VKM": s["vkm"],
                 "Arbeit": s["arbeit"], "hod": s["hodiny"], "radek": gesamt,
                 "chybi": ("FLOOR %s!" % floor if floor_hit else "-")})
    res["rows"] = rows
    return res


def compute_profile_from_cmd(rest: str) -> dict:
    """@@KALKABS profil=nass kw=15 | REGCIS*QTY, REGCIS*QTY, …"""
    profil = None; kw = None
    head, _, body = rest.partition("|")
    for tok in head.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            if k == "profil": profil = v.strip()
            elif k == "kw": kw = v.strip()
    bom = []
    for part in body.split(","):
        part = part.strip()
        if not part:
            continue
        reg, q = (part.rsplit("*", 1) if "*" in part else (part, "1"))
        try:
            qn = float(q)
        except Exception:
            qn = 1.0
        bom.append({"reg_cis": reg.strip(), "qty": qn})
    return compute_profile(bom, profil, kw)


# ── RegCisHeo převodník (EC_RegCisDEF → Cloud) — Vize 1 etapa A (Claude C23, 18.7.2026) ──
# Naše objednací číslo = "<PREFIX> <obj. číslo výrobce>" (SIE 6ES7…). EC_RegCisDEF (přehled 127)
# mapuje Vyrobce → RegCisZkratka (prefix) + normalizační pravidla. Zrcadlíme do tenant.kalk_regcis_def.

def _regcis_ensure_table(sd):
    from sqlalchemy import text as _t
    sd.execute(_t(
        "CREATE TABLE IF NOT EXISTS tenant.kalk_regcis_def ("
        " ec_id int PRIMARY KEY, vyrobce text, zkratka text, obsahuje_text text,"
        " priklad_vyr text, priklad_helios text, velka_pismena text, zadne_mezery text,"
        " nahradit_o_za_0 text, doplnit_nulami_na int, pouziva_alt text,"
        " synced_at timestamptz NOT NULL DEFAULT now())"))
    sd.execute(_t("CREATE INDEX IF NOT EXISTS ix_kalk_regcis_zkratka ON tenant.kalk_regcis_def (zkratka)"))
    try:
        sd.execute(_t("GRANT SELECT ON tenant.kalk_regcis_def TO PUBLIC"))
    except Exception:
        pass


def sync_regcis_def() -> dict:
    """Zrcadlí EC_RegCisDEF (DB_EC) → tenant.kalk_regcis_def. Idempotentní (DELETE+INSERT)."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    rows = _ec(
        "SELECT ID, Vyrobce, RegCisZkratka, ObsahujeText, PrikladRegCisVyrobce, PrikladRegCisHelios,"
        " VsechnaVelkaPismena, ZadneMezery, NahraditOza0, DoplnitNulamiZlevaNa,"
        " PouzivaTakeAlternativRegCis FROM EC_RegCisDEF")
    sd = get_data_session()
    try:
        _regcis_ensure_table(sd)
        sd.execute(_t("DELETE FROM tenant.kalk_regcis_def"))
        n = 0
        for r in rows:
            def _s(v):
                return None if v is None else str(v).strip()
            sd.execute(_t(
                "INSERT INTO tenant.kalk_regcis_def (ec_id,vyrobce,zkratka,obsahuje_text,priklad_vyr,"
                "priklad_helios,velka_pismena,zadne_mezery,nahradit_o_za_0,doplnit_nulami_na,pouziva_alt) "
                "VALUES (:i,:v,:z,:o,:pv,:ph,:vp,:zm,:no,:dn,:pa)"),
                {"i": _int(r.get("ID")), "v": _s(r.get("Vyrobce")), "z": _s(r.get("RegCisZkratka")),
                 "o": _s(r.get("ObsahujeText")), "pv": _s(r.get("PrikladRegCisVyrobce")),
                 "ph": _s(r.get("PrikladRegCisHelios")), "vp": _s(r.get("VsechnaVelkaPismena")),
                 "zm": _s(r.get("ZadneMezery")), "no": _s(r.get("NahraditOza0")),
                 "dn": _int(r.get("DoplnitNulamiZlevaNa")), "pa": _s(r.get("PouzivaTakeAlternativRegCis"))})
            n += 1
        sd.commit()
        return {"ok": True, "vlozeno": n}
    except Exception:
        sd.rollback()
        raise
    finally:
        sd.close()


def _truthy(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "ano", "y", "yes", "x") if v is not None else False


def regcis_build(vyrobce: str, raw_code: str) -> dict:
    """Z (výrobce + syrové obj. číslo) složí RegCisHeo = '<zkratka> <normalizovaný kód>'
    dle pravidel EC_RegCisDEF. Výrobce se hledá dle vyrobce/zkratky/ObsahujeText (case-insens.)."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    v = (vyrobce or "").strip()
    code = (raw_code or "").strip()
    sd = get_data_session()
    try:
        row = sd.execute(_t(
            "SELECT zkratka, velka_pismena, zadne_mezery, nahradit_o_za_0, doplnit_nulami_na "
            "FROM tenant.kalk_regcis_def "
            "WHERE upper(vyrobce)=upper(:v) OR upper(zkratka)=upper(:v) "
            "   OR (obsahuje_text IS NOT NULL AND obsahuje_text<>'' AND upper(:v) LIKE '%'||upper(obsahuje_text)||'%') "
            "ORDER BY CASE WHEN upper(zkratka)=upper(:v) THEN 0 WHEN upper(vyrobce)=upper(:v) THEN 1 ELSE 2 END "
            "LIMIT 1"), {"v": v}).first()
    finally:
        sd.close()
    if not row:
        return {"ok": False, "error": "výrobce '%s' není v EC_RegCisDEF (spusť @@KALKREGCIS SYNC)" % v}
    zkratka, velka, mezery, oza0, dopl = row
    c = code
    if _truthy(velka):
        c = c.upper()
    if _truthy(oza0):
        c = c.replace("O", "0").replace("o", "0")
    if _truthy(mezery):
        c = c.replace(" ", "")
    if dopl and str(dopl).isdigit() and int(dopl) > 0:
        c = c.zfill(int(dopl))
    regcisheo = ("%s %s" % (zkratka, c)).strip()
    return {"ok": True, "regcisheo": regcisheo, "zkratka": zkratka, "kod": c}


def regcis_cmd(rest: str) -> dict:
    """@@KALKREGCIS SYNC | LIST [filtr] | BUILD <vyrobce> <syrove_cislo>"""
    parts = (rest or "").split(None, 2)
    sub = (parts[0].upper() if parts else "LIST")
    if sub == "SYNC":
        _r = sync_regcis_def()
        return {"ok": True, "columns": ["vysledek"], "rows": [["SYNC ok — vlozeno %s radku" % _r.get("vlozeno")]]}
    if sub == "BUILD":
        if len(parts) < 3:
            return {"ok": False, "error": "@@KALKREGCIS BUILD <vyrobce> <syrove_cislo>"}
        _b = regcis_build(parts[1], parts[2])
        if _b.get("ok"):
            return {"ok": True, "columns": ["regcisheo", "zkratka", "kod"],
                    "rows": [[_b["regcisheo"], _b["zkratka"], _b["kod"]]]}
        return {"ok": True, "columns": ["chyba"], "rows": [[_b.get("error", "?")]]}
    # LIST
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    q = (parts[1].strip() if len(parts) > 1 else "")
    sd = get_data_session()
    try:
        where = ""
        params = {}
        if q:
            where = "WHERE upper(vyrobce) LIKE :q OR upper(zkratka) LIKE :q"
            params["q"] = "%" + q.upper() + "%"
        rr = sd.execute(_t(
            "SELECT vyrobce, zkratka, obsahuje_text, doplnit_nulami_na FROM tenant.kalk_regcis_def "
            + where + " ORDER BY zkratka LIMIT 200"), params).fetchall()
        cnt = sd.execute(_t("SELECT count(*) FROM tenant.kalk_regcis_def")).scalar()
    finally:
        sd.close()
    return {"ok": True, "columns": ["vyrobce", "zkratka", "obsahuje_text", "doplnit_nulami_na"],
            "rows": [[a, b, c, str(d) if d is not None else ""] for (a, b, c, d) in rr],
            "celkem": cnt}


# ── Vize 1 etapa B: materiálová cena z PŘÍJEMKY (TabPohybyZbozi ř.110) + korekce ceníkem ──
# (Claude C23, 18.7.2026). Klíč = RegCisHeo. Pravidlo: poslední nákupka z faktury/příjemky,
# korigovaná Velkým ceníkem kvůli zdražování → cena = max(příjemka, ceník), flag při rozporu.

def _norm_kat(code: str) -> str:
    import re as _re
    return _re.sub(r"\s+", "", (code or "")).upper()


def _prijemka_prices(reg_list) -> dict:
    """Pro seznam RegCisHeo vrátí poslední nákupku z příjemky (DB_EC TabPohybyZbozi ř.110).
    Jedna cena per díl = globálně nejnovější příjemka přes všechny sklad. karty dílu."""
    regs = [r for r in {(x or "").strip() for x in reg_list} if r]
    if not regs:
        return {}
    vals = ",".join("N'%s'" % r.replace("'", "''") for r in regs)
    rows = _ec(
        "SELECT k.RegCis, k.EMJ, k.MJVstup, k.MjPocetVstup, k.BaleniTXT, "
        "pp.JCbezDaniVal, pp.JCbezDaniKC, CONVERT(varchar(10),pp.DatPorizeni,23) AS dat "
        "FROM TabKmenZbozi k OUTER APPLY ("
        " SELECT TOP 1 P.JCbezDaniVal, P.JCbezDaniKC, P.DatPorizeni"
        " FROM TabPohybyZbozi P"
        " JOIN TabStavSkladu s ON s.ID = P.IDZboSklad AND s.IDKmenZbozi = k.ID"
        " LEFT JOIN TabDokladyZbozi D ON P.IDDoklad = D.ID"
        " WHERE P.DruhPohybuZbo = 0 AND P.JCBezDaniVal <> 0 AND D.RadaDokladu = 110"
        " ORDER BY P.DatPorizeni DESC) pp "
        "WHERE k.RegCis IN (" + vals + ")")
    out = {}
    for r in rows:
        rc = (r.get("RegCis") or "").strip()
        if rc:
            out[rc] = {"val": _num(r.get("JCbezDaniVal")), "kc": _num(r.get("JCbezDaniKC")), "dat": r.get("dat"),
                       "emj": (r.get("EMJ") or "").strip() or None, "mj_vstup": (r.get("MJVstup") or "").strip() or None,
                       "mj_pocet": _num(r.get("MjPocetVstup")), "baleni_txt": (r.get("BaleniTXT") or "").strip() or None}
    return out


def _cenik_prices(reg_list) -> dict:
    """Pro seznam RegCisHeo vrátí net cenu z Velkého ceníku (nejnovější import per dodavatel)."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    norm_map = {}
    for r in reg_list:
        n = _norm_kat(r)
        if n:
            norm_map.setdefault(n, r)
    if not norm_map:
        return {}
    sd = get_data_session()
    try:
        rows = sd.execute(_t(
            "WITH latest AS (SELECT vyrobce, max(id) AS id FROM proj.cenik_import WHERE tenant_id=2 GROUP BY vyrobce) "
            "SELECT p.kat_kod_norm, p.net_price, p.list_price, p.mj, p.mena, i.vyrobce "
            "FROM proj.cenik_polozka p JOIN latest l ON l.id=p.import_id JOIN proj.cenik_import i ON i.id=p.import_id "
            "WHERE p.tenant_id=2 AND p.kat_kod_norm = ANY(:ns)"), {"ns": list(norm_map.keys())}).fetchall()
    finally:
        sd.close()
    out = {}
    for kk, net, lst, mj, mena, vyr in rows:
        reg = norm_map.get(kk)
        if reg and reg not in out:
            out[reg] = {"net": float(net) if net is not None else None,
                        "list": float(lst) if lst is not None else None,
                        "mj": (mj or "").strip() or None, "mena": mena, "vyrobce": vyr}
    return out


def price_bom(bom: list) -> dict:
    """bom=[{'reg_cis','qty'}]. Pro každý díl: příjemka + ceník → cena=max(oba), flag rozporu.
    Vrací řádky + souhrn (materiál dle ceny, dle příjemky, dle ceníku)."""
    regs = [str(it.get("reg_cis") or "").strip() for it in bom]
    prij = _prijemka_prices(regs)
    cen = _cenik_prices(regs)
    rows = []
    sum_cena = sum_prij = sum_cen = 0.0
    for it in bom:
        reg = str(it.get("reg_cis") or "").strip()
        qty = float(it.get("qty") or 0)
        p = prij.get(reg) or {}
        c = cen.get(reg) or {}
        pval = p.get("val")
        cnet = c.get("net")
        pdat = p.get("dat")
        # staří příjemky (kvůli zdražování): starší než 12 měsíců = nedůvěřuj, opři se o ceník
        stale = False
        stari_m = None
        if pdat:
            try:
                from datetime import datetime as _dtp, date as _datep
                _d0 = _dtp.strptime(pdat, "%Y-%m-%d").date()
                _dage = (_datep.today() - _d0).days
                stari_m = _dage // 30
                stale = _dage > 365
            except Exception:
                pass
        # cena: čerstvá příjemka → max(příjemka, ceník); stará → ceník (je-li); flag
        # balné (kvůli zmatkům v jednotkách — LAPP/RIT/PHO/WEI): EMJ + nákupní MJ × počet ks v balení
        _emj = p.get("emj"); _mjv = p.get("mj_vstup"); _mjp = p.get("mj_pocet"); _cmj = c.get("mj")
        balne = "EMJ=%s | vstup %s×%s | cenikMJ=%s" % (
            _emj or "?", _mjv or "?", (("%g" % _mjp) if _mjp else "?"), _cmj or "?")
        if pval is not None and cnet is not None:
            _diff = abs(pval - cnet) / min(pval, cnet) if min(pval, cnet) > 0 else 999.0
            if _diff > 0.60:
                # rozdíl >60 % → skoro jistě balné jednotky (LAPP/RIT/PHO/WEI); nedůvěřuj max,
                # opři se o ceník (per-ks list) a označ VYKŘIČNÍKEM k ručnímu vyřešení balného
                cena = cnet
                flag = "! BALNE %.0f%% (prij %.2f vs cenik %.2f)" % (_diff * 100, pval, cnet)
            elif stale:
                cena = cnet
                flag = "stara_prijemka(%sm)->cenik" % (stari_m if stari_m is not None else "?")
            elif cnet > pval * 1.001:
                cena = cnet
                flag = "zdrazeno(cenik>prijemka)"
            elif pval > cnet * 1.001:
                cena = pval
                flag = "prijemka>cenik"
            else:
                cena = pval
                flag = "ok"
        elif pval is not None:
            cena = pval
            flag = ("stara_prijemka(%sm)_bez_ceniku" % stari_m) if stale else "jen_prijemka"
        elif cnet is not None:
            cena = cnet
            flag = "jen_cenik"
        else:
            cena = None
            flag = "NENACENEN"
        if cena is not None:
            sum_cena += cena * qty
        if pval is not None:
            sum_prij += pval * qty
        if cnet is not None:
            sum_cen += cnet * qty
        rows.append({"reg_cis": reg, "qty": qty, "prijemka": pval, "prij_dat": p.get("dat"),
                     "cenik_net": cnet, "cena": cena, "flag": flag, "balne": balne})
    n_miss = sum(1 for r in rows if r["flag"] == "NENACENEN")
    return {"ok": True, "radky": rows,
            "souhrn": {"material_cena": round(sum_cena, 2), "material_prijemka": round(sum_prij, 2),
                       "material_cenik": round(sum_cen, 2), "polozek": len(rows), "nenaceneno": n_miss}}


def price_cmd(rest: str) -> dict:
    """@@KALKPRICE <RegCisHeo>*<qty>, <RegCisHeo>*<qty>, …  → příjemka+ceník+cena per díl."""
    bom = []
    for part in (rest or "").split(","):
        part = part.strip()
        if not part:
            continue
        reg, q = (part.rsplit("*", 1) if "*" in part else (part, "1"))
        try:
            qn = float(q)
        except Exception:
            qn = 1.0
        bom.append({"reg_cis": reg.strip(), "qty": qn})
    res = price_bom(bom)
    rows = [[r["reg_cis"], str(r["qty"]),
             ("%.2f" % r["prijemka"]) if r["prijemka"] is not None else "-",
             r.get("prij_dat") or "-",
             ("%.2f" % r["cenik_net"]) if r["cenik_net"] is not None else "-",
             ("%.2f" % r["cena"]) if r["cena"] is not None else "-", r["flag"], r.get("balne", "")] for r in res["radky"]]
    su = res["souhrn"]
    rows.append(["== SOUČET ==", "", "%.2f" % su["material_prijemka"], "",
                 "%.2f" % su["material_cenik"], "%.2f" % su["material_cena"],
                 "nenac=%d/%d" % (su["nenaceneno"], su["polozek"]), ""])
    return {"ok": True, "columns": ["reg_cis", "qty", "prijemka", "prij_dat", "cenik_net", "cena", "flag", "balne"], "rows": rows}


# ── Vize 1 GESAMT zevnitř: v1 materiál (příjemka+ceník) + koeficienty z EC → profil ──
# (Claude C23, 18.7.2026). Koeficient per díl z EC_KalkKoeficienty přes RegCisHeo→TabKmenZbozi.ID.

def _coef_ec(reg_list) -> dict:
    regs = [r for r in {(x or "").strip() for x in reg_list} if r]
    if not regs:
        return {}
    vals = ",".join("N'%s'" % r.replace("'", "''") for r in regs)
    rows = _ec(
        "SELECT k.RegCis, ko.K_VKM, ko.K_ARB FROM TabKmenZbozi k "
        "JOIN EC_KalkKoeficienty ko ON ko.IDKmenZbozi = k.ID "
        "WHERE k.RegCis IN (" + vals + ")")
    out = {}
    for r in rows:
        rc = (r.get("RegCis") or "").strip()
        if rc and rc not in out:
            out[rc] = {"k_vkm": _num(r.get("K_VKM")), "k_arb": _num(r.get("K_ARB"))}
    return out


def compute_absv1(bom: list, profil_kod, kw=None) -> dict:
    """GESAMT zevnitř: materiál z v1 (příjemka+ceník), VKM/Arbeit z EC koeficientů, profil marže/floor/fix."""
    p = PROFILY.get((profil_kod or "").lower())
    if not p:
        return {"ok": False, "error": "neznámý profil '%s' (%s)" % (profil_kod, ", ".join(PROFILY))}
    pr = price_bom(bom)
    price_by = {r["reg_cis"]: r for r in pr["radky"]}
    coef = _coef_ec([it.get("reg_cis") for it in bom])
    bvkm = p["vkm"]; barb = p["arb"]
    rows = []
    mat = vkm_t = arb_t = 0.0
    chybi_cena = chybi_koef = 0
    for it in bom:
        reg = str(it.get("reg_cis") or "").strip()
        qty = float(it.get("qty") or 0)
        pl = price_by.get(reg, {})
        cena = pl.get("cena")
        flag = pl.get("flag")
        co = coef.get(reg, {})
        kv = co.get("k_vkm"); ka = co.get("k_arb")
        if cena is None:
            chybi_cena += 1
        if kv is None and ka is None:
            chybi_koef += 1
        vkm = round((kv or 0) * bvkm, 4)
        arb = round((ka or 0) * barb, 4)
        radek = round(((cena or 0) + vkm + arb) * qty, 2)
        mat += (cena or 0) * qty
        vkm_t += vkm * qty
        arb_t += arb * qty
        rows.append([reg, str(qty), ("%.2f" % cena) if cena is not None else "-",
                     "%.2f" % (vkm * qty), "%.2f" % (arb * qty), "%.2f" % radek, flag or "-"])
    mat = round(mat, 2); vkm_t = round(vkm_t, 2); arb_t = round(arb_t, 2)
    radky_celkem = round(mat + vkm_t + arb_t, 2)
    marze = round(radky_celkem * p["marze"] / 100.0, 2)
    fixni = p["projekt"] + p["revize"] + p["transport"]
    gesamt = round(radky_celkem + marze + fixni, 2)
    floor = p.get("floor", {}).get(str(kw)) if kw is not None else None
    floor_hit = bool(floor and gesamt < floor)
    if floor_hit:
        gesamt = float(floor)
    rows.append(["== SOUČET ==", "", "%.2f" % mat, "%.2f" % vkm_t, "%.2f" % arb_t, "%.2f" % radky_celkem,
                 "chybi cena=%d koef=%d" % (chybi_cena, chybi_koef)])
    rows.append(["== GESAMT ==", p["nazev"][:22],
                 "marze %.0f%%=%.2f" % (p["marze"], marze), "fix=%.0f" % fixni,
                 ("FLOOR %s!" % floor) if floor_hit else "-", "%.2f" % gesamt,
                 "nabidnout %.0f" % (round(gesamt / 10.0) * 10)])
    return {"ok": True, "columns": ["reg_cis", "qty", "material", "VKM", "Arbeit", "radek", "flag"], "rows": rows}


def compute_absv1_from_cmd(rest: str) -> dict:
    """@@KALKABSV1 profil=flex kw=15 | REGCIS*QTY, …  → GESAMT z příjemky+ceníku+EC koeficientů."""
    profil = None; kw = None
    head, _, body = rest.partition("|")
    for tok in head.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            if k == "profil":
                profil = v.strip()
            elif k == "kw":
                kw = v.strip()
    bom = []
    for part in body.split(","):
        part = part.strip()
        if not part:
            continue
        reg, q = (part.rsplit("*", 1) if "*" in part else (part, "1"))
        try:
            qn = float(q)
        except Exception:
            qn = 1.0
        bom.append({"reg_cis": reg.strip(), "qty": qn})
    return compute_absv1(bom, profil, kw)


# ── Vydané poptávky (řada 940): boční tabulka s cenami nabídek dodavatelů (strategie-owned) ──
# (Claude C23, 18.7.2026). ec_doklad_zbozi vlastní Marti-AI (nelze ALTER strategie) → vlastní
# tenant.vypopt_nabidka (src_id → cena/platnost/dodavatel/výrobce/popis/soubor/kontakt + SeznamKalkulací).

def vydane_poptavky_sync() -> dict:
    """Dotáhne z DB_EC (řada 940) EXT pole přijatých nabídek → tenant.vypopt_nabidka (upsert dle src_id)."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    rows = _ec(
        "SELECT d.ID, "
        "CAST(e._Kcen_Cena AS numeric(19,4)) Cena, CONVERT(varchar(10),e._PlatnostDoNabDod,23) PlatnostDo, "
        "CAST(e._Sleva AS numeric(9,2)) Sleva, e._OrgNazevNabDod Dodavatel, e._VyrobceNab Vyrobce, "
        "e._PopisNabDod Popis, e._PoznamkaVyvojar Soubor, e._KontaktJmenoNabDod KontaktJmeno, "
        "e._KontaktNabDod KontaktEmail, e._PoznamkaExt CisloECImport, "
        "(SELECT STRING_AGG(KH.CisloKalkulace, ',') FROM TabDokladyZbozi NB "
        "  LEFT JOIN EC_KalkulaceHlav KH ON KH.IDDoklad=NB.ID "
        "  LEFT JOIN EC_DokladyVazby DV ON DV.ID_Odkud=NB.ID WHERE DV.ID_Kam=d.ID) SeznamKalk "
        "FROM TabDokladyZbozi d LEFT JOIN TabDokladyZbozi_EXT e ON e.ID=d.ID "
        "WHERE d.RadaDokladu='940' AND d.DatPorizeni >= '2024-01-01'")
    sd = get_data_session()
    try:
        sd.execute(_t(
            "CREATE TABLE IF NOT EXISTS tenant.vypopt_nabidka ("
            " src_id bigint PRIMARY KEY, nab_cena numeric(19,4), nab_platnost_do date, nab_sleva numeric(9,2),"
            " nab_dodavatel text, nab_vyrobce text, nab_popis text, nab_soubor text,"
            " nab_kontakt_jmeno text, nab_kontakt_email text, nab_cislo_ec_import text,"
            " seznam_kalkulaci text, synced_at timestamptz NOT NULL DEFAULT now())"))
        try:
            sd.execute(_t("GRANT SELECT ON tenant.vypopt_nabidka TO PUBLIC"))
        except Exception:
            pass

        def _s(v):
            return (str(v).replace("\x00", "").strip() or None) if v is not None else None
        n = 0
        for r in rows:
            sid = _int(r.get("ID"))
            if sid is None:
                continue
            sd.execute(_t(
                "INSERT INTO tenant.vypopt_nabidka (src_id,nab_cena,nab_platnost_do,nab_sleva,nab_dodavatel,"
                "nab_vyrobce,nab_popis,nab_soubor,nab_kontakt_jmeno,nab_kontakt_email,nab_cislo_ec_import,"
                "seznam_kalkulaci,synced_at) VALUES (:sid,:c,:pl,:sl,:dod,:vyr,:pop,:sou,:kj,:ke,:cim,:sk,now()) "
                "ON CONFLICT (src_id) DO UPDATE SET nab_cena=excluded.nab_cena, nab_platnost_do=excluded.nab_platnost_do, "
                "nab_sleva=excluded.nab_sleva, nab_dodavatel=excluded.nab_dodavatel, nab_vyrobce=excluded.nab_vyrobce, "
                "nab_popis=excluded.nab_popis, nab_soubor=excluded.nab_soubor, nab_kontakt_jmeno=excluded.nab_kontakt_jmeno, "
                "nab_kontakt_email=excluded.nab_kontakt_email, nab_cislo_ec_import=excluded.nab_cislo_ec_import, "
                "seznam_kalkulaci=excluded.seznam_kalkulaci, synced_at=now()"),
                {"sid": sid, "c": _num(r.get("Cena")), "pl": (r.get("PlatnostDo") or None), "sl": _num(r.get("Sleva")),
                 "dod": _s(r.get("Dodavatel")), "vyr": _s(r.get("Vyrobce")), "pop": _s(r.get("Popis")),
                 "sou": _s(r.get("Soubor")), "kj": _s(r.get("KontaktJmeno")), "ke": _s(r.get("KontaktEmail")),
                 "cim": _s(r.get("CisloECImport")), "sk": _s(r.get("SeznamKalk"))})
            n += 1
        sd.commit()
        return {"ok": True, "nacteno_z_ec": len(rows), "upsertovano": n}
    except Exception:
        sd.rollback()
        raise
    finally:
        sd.close()


def vydane_poptavky_list(rest: str = "") -> dict:
    """@@VYPOPT LIST [filtr] — přehled vydaných poptávek (940) + ceny nabídek dodavatelů."""
    from core.database_data import get_data_session
    from sqlalchemy import text as _t
    q = (rest or "").strip()
    sd = get_data_session()
    try:
        where = "WHERE d.rada='940'"
        params = {}
        if q:
            where += " AND (upper(v.nab_dodavatel) LIKE :q OR upper(v.nab_vyrobce) LIKE :q OR upper(d.nazev) LIKE :q)"
            params["q"] = "%" + q.upper() + "%"
        rr = sd.execute(_t(
            "SELECT d.cislo, v.nab_dodavatel, v.nab_vyrobce, v.nab_cena, v.nab_platnost_do, "
            "left(coalesce(v.nab_popis, d.nazev, ''), 30) AS popis, v.seznam_kalkulaci "
            "FROM tenant.ec_doklad_zbozi d LEFT JOIN tenant.vypopt_nabidka v ON v.src_id=d.src_id "
            + where + " ORDER BY d.dat_porizeni DESC LIMIT 40"), params).fetchall()
    finally:
        sd.close()
    return {"ok": True,
            "columns": ["cislo", "dodavatel", "vyrobce", "cena", "platnost", "popis", "kalkulace"],
            "rows": [[a, b or "-", c or "-", ("%.2f" % d) if d is not None else "-",
                      (str(e) if e else "-"), f or "-", g or "-"] for (a, b, c, d, e, f, g) in rr]}


def vypopt_cmd(rest: str) -> dict:
    """@@VYPOPT SYNC | LIST [filtr]"""
    sub = (rest or "").strip()
    if sub.upper().startswith("SYNC"):
        r = vydane_poptavky_sync()
        return {"ok": True, "columns": ["vysledek"],
                "rows": [["SYNC ok — z EC %s, upsertováno %s řádků" % (r.get("nacteno_z_ec"), r.get("upsertovano"))]]}
    arg = sub[4:].strip() if sub.upper().startswith("LIST") else sub
    return vydane_poptavky_list(arg)
