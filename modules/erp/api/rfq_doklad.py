"""
RFQ — zakládání dokladu VYDANÉ POPTÁVKY (řada 940) v DB_EC — Claude ID23, 18. 7. 2026.

Marti item 2: doklad NEinsertujeme přímo do TabDokladyZbozi. EUROSOFT má vlastní
ověřené Helios procedury (Marti 18.7. dodal):

  vytvoření:  EXEC dbo.EC_GenVydanouPoptavku @IDENT OUTPUT, @Message OUTPUT
              → založí prázdný doklad řady 940 (správné číslování/EXT/…), vrátí ID.
  smazání:    smaž vazby EC_DokladyVazby (nabídky 910) + EXEC dbo.EC_SmazVydanouPoptavku @IDDoklad, @Message OUTPUT

Naše role po vygenerování = UPDATE běžných fieldů (dodavatel CisloOrg, PopisDodavky,
Text1, Poznámka, Mena…) — to Marti povolil dělat napřímo. Cenová/nabídková EXT pole
(v TabDokladyZbozi_EXT) doplníme až po napojení příjmu nabídek (po konzultaci s Eliškou).

Zápis do DB_EC jde přes EUROSOFT MCP (`strategie_query_raw`), NE přes read-only most.
"""
from __future__ import annotations

import json

from core.logging import get_logger

logger = get_logger("erp.rfq_doklad")


def _mcp():
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    return get_eurosoft_mcp_client()


def _int(v):
    try:
        return int(v)
    except Exception:
        return None


def _ec_raw(sql: str) -> dict:
    """strategie_query_raw na DB_EC → celý dict {ok, rows, message}."""
    mcp = _mcp()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP klient není dostupný")
    raw = mcp.call_tool_sync(
        full_name="eurosoft_strategie_query_raw",
        arguments={"sql": sql, "db_name": "DB_EC"},
        conversation_id=None,
    )
    res = json.loads(raw) if isinstance(raw, str) else raw
    return res if isinstance(res, dict) else {"ok": False, "error": "neočekávaný tvar odpovědi", "rows": res}


def _q(s) -> str:
    """N'...' literal se zdvojenými apostrofy."""
    if s is None:
        return "NULL"
    return "N'" + str(s).replace("'", "''") + "'"


# ── PROBE: ověří, že MCP guard pustí DECLARE/SELECT batch (0 side-effect) ────
def probe() -> dict:
    sql = "DECLARE @x int = 1 SELECT @x AS probe, CAST(@@VERSION AS nvarchar(60)) AS ver"
    res = _ec_raw(sql)
    return {
        "ok": bool(res.get("ok")),
        "rows": res.get("rows"),
        "error": res.get("message") or res.get("error"),
    }


# ── marker tabulka v st. (zachycení @IDENT přes write-režim MCP) ────────────
# MCP strategie_query_raw ve WRITE režimu (EXEC/UPDATE/INSERT) zahazuje result-sety
# → OUTPUT @IDENT z trailing SELECTu nedostaneme. Proto @IDENT zapíšeme ve stejném
# write-volání do st.rfq_gen_marker (do st. smíme) a druhým SELECT-voláním čteme zpět.
def _ensure_marker() -> None:
    _ec_raw(
        "IF OBJECT_ID('st.rfq_gen_marker') IS NULL "
        "CREATE TABLE st.rfq_gen_marker("
        "id int IDENTITY(1,1) PRIMARY KEY, nonce nvarchar(64), ident int, "
        "msg nvarchar(255), created datetime DEFAULT GETDATE())"
    )


def gen_vydana_poptavka() -> dict:
    import uuid
    _ensure_marker()
    nonce = uuid.uuid4().hex
    # write-volání: EXEC proc + zápis IDENT do markeru (nonce-keyed)
    sql = (
        "DECLARE @IDENT int, @Message nvarchar(255) "
        "EXEC [dbo].[EC_GenVydanouPoptavku] @IDENT = @IDENT OUTPUT, @Message = @Message OUTPUT "
        "INSERT INTO st.rfq_gen_marker(nonce, ident, msg) VALUES(N'%s', @IDENT, @Message)" % nonce
    )
    res = _ec_raw(sql)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    # SELECT-volání: přečti IDENT zpět podle nonce
    rb = _ec_raw("SELECT TOP 1 ident, msg FROM st.rfq_gen_marker WHERE nonce=N'%s' ORDER BY id DESC" % nonce)
    rows = rb.get("rows") or []
    if not rows:
        return {"ok": False, "error": "marker nevrátil IDENT (nonce=%s)" % nonce}
    r = rows[0]
    ident = _int(r.get("ident"))
    if not ident:
        return {"ok": False, "error": "IDENT je prázdný — proc doklad nezaložila (nonce=%s)" % nonce}
    return {"ok": True, "ident": ident, "message": r.get("msg"), "nonce": nonce}


# ── smazání poptávky (úklid testů) ──────────────────────────────────────────
def smaz_vydana_poptavka(doklad_id: int) -> dict:
    did = int(doklad_id)
    # POJISTKA (Marti 18.7.): ten delete na EC_DokladyVazby maže vazby poptávka↔nabídky (910).
    # Nikdy ho nespustíme na cizí doklad → ověříme, že ID je opravdu řada 940, jinak odmítneme.
    chk = _ec_raw("SELECT RadaDokladu AS r FROM TabDokladyZbozi WHERE ID = %d" % did)
    crows = chk.get("rows") or []
    if not crows:
        return {"ok": False, "error": "doklad ID=%d neexistuje" % did}
    rada = str((crows[0] or {}).get("r") or "").strip()
    if rada != "940":
        return {"ok": False, "error": "ID=%d NENÍ vydaná poptávka (řada=%s) — mazání odmítnuto" % (did, rada)}
    sql = (
        "DECLARE @Message nvarchar(200) DECLARE @ID int = %d "
        "delete from EC_DokladyVazby where id in (select V.ID from EC_DokladyVazby V "
        "left outer join TabDokladyZbozi as Nabidka on Nabidka.ID=V.ID_Odkud and Nabidka.RadaDokladu='910' "
        "where V.ID_Kam=@ID and Nabidka.ID is not null) "
        "EXEC EC_SmazVydanouPoptavku @IDDoklad = @ID, @Message = @Message OUTPUT "
        "SELECT @Message AS Message" % did
    )
    res = _ec_raw(sql)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    rows = res.get("rows") or []
    return {"ok": True, "message": (rows[0].get("Message") if rows else None)}


# ── UPDATE běžných fieldů, které se na poptávce reálně vyplňují ──────────────
# Header (TabDokladyZbozi): CisloOrg=dodavatel, TerminDodavkyDat=pož. termín, Mena, CisloZakazky.
# EXT (TabDokladyZbozi_EXT): _OznPrjZakaznik = "Název poptávky" (popis co poptáváme).
def update_poptavka_header(
    doklad_id: int,
    cislo_org: str | None = None,
    termin_dat: str | None = None,   # 'YYYY-MM-DD'
    mena: str | None = None,
    cislo_zakazky: str | None = None,
    cislo_zam: int | None = None,      # řešitel = TabCisZam.Cislo
    kontakt_osoba: int | None = None,  # kontaktní osoba dodavatele = TabCisKOs.ID
) -> dict:
    sets = []
    if cislo_org is not None:
        sets.append("CisloOrg = %s" % _q(cislo_org))
    if termin_dat is not None:
        # "PožadovanýTermín" (TerminDodavkyDat) je computed z [Splatnost] → píšeme Splatnost
        sets.append("Splatnost = %s" % _q(termin_dat))
    if mena is not None:
        sets.append("Mena = %s" % _q(mena))
    if cislo_zakazky is not None:
        sets.append("CisloZakazky = %s" % _q(cislo_zakazky))
    if cislo_zam is not None:
        sets.append("CisloZam = %d" % int(cislo_zam))
    if kontakt_osoba is not None:
        sets.append("KontaktOsoba = %d" % int(kontakt_osoba))
    if not sets:
        return {"ok": False, "error": "žádné pole hlavičky k updatu"}
    sql = "UPDATE TabDokladyZbozi SET %s WHERE ID = %d" % (", ".join(sets), int(doklad_id))
    res = _ec_raw(sql)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    return {"ok": True}


def update_poptavka_ext(doklad_id: int, nazev_poptavky: str) -> dict:
    """_OznPrjZakaznik (Název poptávky) — UPDATE, nebo INSERT řádku EXT když chybí."""
    did = int(doklad_id)
    sql = (
        "IF EXISTS(SELECT 1 FROM TabDokladyZbozi_EXT WHERE ID=%d) "
        "UPDATE TabDokladyZbozi_EXT SET _OznPrjZakaznik=%s WHERE ID=%d "
        "ELSE INSERT INTO TabDokladyZbozi_EXT(ID, _OznPrjZakaznik) VALUES(%d, %s)"
        % (did, _q(nazev_poptavky), did, did, _q(nazev_poptavky))
    )
    res = _ec_raw(sql)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    return {"ok": True}


# ── přístup do adresáře dokumentů poptávky na sdíleném disku ────────────────
# Každý doklad má složku \\192.168.30.11\data\poptavky_V\<doklad> (= D:\Data\poptavky_V\<doklad>
# na EC-SERVER2). MCP FS bere LOKÁLNÍ kořen D:\Data\…, ne UNC přes hostname (gotcha 3.7.).
_POPTAVKY_ROOT = "D:\\Data\\poptavky_V"


def list_poptavka_dir(doklad: str) -> dict:
    from modules.erp.api.directories import _eu_list
    return _eu_list(_POPTAVKY_ROOT, str(doklad).strip())


def save_file_to_poptavka_dir(doklad: str, filename: str, content_text: str) -> dict:
    """Uloží textový soubor (nabídku/e-mail) do složky poptávky na sdíleném disku."""
    import base64
    from modules.erp.api.directories import _eu_write
    b64 = base64.b64encode((content_text or "").encode("utf-8")).decode("ascii")
    relpath = "%s\\%s" % (str(doklad).strip(), filename)
    r = _eu_write(_POPTAVKY_ROOT, relpath, b64)
    return r if isinstance(r, dict) else {"ok": True}


# ── kontaktní osoby dodavatele (přehled 107) — komu poptávku poslat ─────────
def find_org_contacts(cislo_org: str) -> list[dict]:
    sql = (
        "SELECT DISTINCT KO.ID AS id, (KO.Prijmeni+' '+ISNULL(KO.Jmeno,'')) AS osoba, "
        "VKO.Funkce AS funkce, em.Spojeni AS email, "
        "COALESCE(tel.Spojeni, mob.Spojeni) AS tel "
        "FROM TabCisKOs KO "
        "LEFT JOIN TabCisKOs_EXT KOe ON KOe.ID=KO.ID "
        "JOIN TabVztahOrgKOs VKO ON VKO.IDCisKOs=KO.ID "
        "JOIN TabCisOrg org ON org.ID=VKO.IDOrg "
        "LEFT JOIN TabKontakty em  ON KO.ID=em.IDCisKOs  AND em.Druh=6  AND em.Kam=0 AND em.IDVztahKOsOrg IS NULL AND em.Prednastaveno=1 "
        "LEFT JOIN TabKontakty tel ON KO.ID=tel.IDCisKOs AND tel.Druh=1 AND tel.IDVztahKOsOrg IS NULL AND tel.Prednastaveno=1 "
        "LEFT JOIN TabKontakty mob ON KO.ID=mob.IDCisKOs AND mob.Druh=2 AND mob.Kam=0 AND mob.IDVztahKOsOrg IS NULL AND mob.Prednastaveno=1 "
        "WHERE ISNULL(KOe._neaktivni,0)<>1 AND org.CisloOrg=%s "
        "ORDER BY osoba" % _q(cislo_org)
    )
    res = _ec_raw(sql)
    return res.get("rows") or []


def read_poptavka(doklad_id: int) -> dict:
    """Přečti poptávku tak, jak ji vidí přehled (header + EXT název)."""
    did = int(doklad_id)
    sql = (
        "SELECT dbo.EC_GetDoklad(d.ID) AS doklad, d.CisloOrg, org.Nazev AS firma, "
        "de._OznPrjZakaznik AS nazev_poptavky, "
        "CONVERT(varchar(10),d.TerminDodavkyDat,23) AS termin, d.Mena, d.CisloZakazky, d.Autor "
        "FROM TabDokladyZbozi d "
        "LEFT JOIN TabCisOrg org ON d.CisloOrg=org.CisloOrg "
        "LEFT JOIN TabDokladyZbozi_EXT de ON de.ID=d.ID WHERE d.ID=%d" % did
    )
    res = _ec_raw(sql)
    rows = res.get("rows") or []
    return rows[0] if rows else {}


def update_poptavka_nabidka(
    doklad_id: int,
    cena: float | None = None,
    platnost_do: str | None = None,   # 'YYYY-MM-DD'
    dodavatel: str | None = None,
    popis: str | None = None,
    cislo_nabidky: str | None = None,
    vyrobce: str | None = None,
    druh_ceny: int | None = None,   # 1=Obecná, 2=Projektová, 3=Zákazník
) -> dict:
    """
    Zapíše přijatou NABÍDKU dodavatele do EXT polí poptávky (TabDokladyZbozi_EXT):
    _Kcen_Cena, _PlatnostDoNabDod, _OrgNazevNabDod, _PopisNabDod, _CisloNabidkyDodavatele,
    _VyrobceNab, _TypCenyNabDod(+_TEXT).
    """
    _DRUH = {1: "Obecná", 2: "Projektová", 3: "Zákazník"}
    did = int(doklad_id)
    sets = []
    if cena is not None:
        sets.append("_Kcen_Cena = %s" % float(cena))
    if platnost_do is not None:
        sets.append("_PlatnostDoNabDod = %s" % _q(platnost_do))
    if dodavatel is not None:
        sets.append("_OrgNazevNabDod = %s" % _q(dodavatel))
    if popis is not None:
        sets.append("_PopisNabDod = %s" % _q(popis))
    if cislo_nabidky is not None:
        sets.append("_CisloNabidkyDodavatele = %s" % _q(cislo_nabidky))
    if vyrobce is not None:
        sets.append("_VyrobceNab = %s" % _q(vyrobce))
    if druh_ceny is not None:
        # _TypCenyNabDod_TEXT je computed z kódu → píšeme jen kód
        sets.append("_TypCenyNabDod = %d" % int(druh_ceny))
    if not sets:
        return {"ok": False, "error": "žádné pole nabídky k updatu"}
    setclause = ", ".join(sets)
    # sestav i INSERT variantu (stejná pole)
    cols = []
    vals = []
    if cena is not None:
        cols.append("_Kcen_Cena"); vals.append(str(float(cena)))
    if platnost_do is not None:
        cols.append("_PlatnostDoNabDod"); vals.append(_q(platnost_do))
    if dodavatel is not None:
        cols.append("_OrgNazevNabDod"); vals.append(_q(dodavatel))
    if popis is not None:
        cols.append("_PopisNabDod"); vals.append(_q(popis))
    if cislo_nabidky is not None:
        cols.append("_CisloNabidkyDodavatele"); vals.append(_q(cislo_nabidky))
    if vyrobce is not None:
        cols.append("_VyrobceNab"); vals.append(_q(vyrobce))
    if druh_ceny is not None:
        cols.append("_TypCenyNabDod"); vals.append(str(int(druh_ceny)))
    sql = (
        "IF EXISTS(SELECT 1 FROM TabDokladyZbozi_EXT WHERE ID=%d) "
        "UPDATE TabDokladyZbozi_EXT SET %s WHERE ID=%d "
        "ELSE INSERT INTO TabDokladyZbozi_EXT(ID, %s) VALUES(%d, %s)"
        % (did, setclause, did, ", ".join(cols), did, ", ".join(vals))
    )
    res = _ec_raw(sql)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    return {"ok": True}


def read_poptavka_nabidka(doklad_id: int) -> dict:
    sql = (
        "SELECT CAST(de._Kcen_Cena AS varchar) AS cena, "
        "CONVERT(varchar(10),de._PlatnostDoNabDod,23) AS platnost, "
        "de._OrgNazevNabDod AS dodavatel, de._PopisNabDod AS popis, "
        "de._CisloNabidkyDodavatele AS cislo_nab "
        "FROM TabDokladyZbozi_EXT de WHERE de.ID=%d" % int(doklad_id)
    )
    res = _ec_raw(sql)
    rows = res.get("rows") or []
    return rows[0] if rows else {}


def _header(doklad_id: int) -> dict:
    """Přečti pár klíčových polí nově založeného dokladu (kontrola)."""
    sql = (
        "SELECT ID, RadaDokladu, PoradoveCislo, dbo.EC_GetDoklad(ID) AS doklad, "
        "CisloOrg, PopisDodavky, Autor, DatPorizeni "
        "FROM TabDokladyZbozi WHERE ID = %d" % int(doklad_id)
    )
    res = _ec_raw(sql)
    rows = res.get("rows") or []
    return rows[0] if rows else {}


# ── @@ příkaz ────────────────────────────────────────────────────────────────
#   @@RFQDOKLAD PROBE                     — bezpečný test MCP write path (0 side-effect)
#   @@RFQDOKLAD TEST                      — gen → přečti → smaž (round-trip, beze stopy)
#   @@RFQDOKLAD GEN                       — jen vygeneruj prázdný doklad, vrať ID (POZOR: reálný)
#   @@RFQDOKLAD SMAZ <id>                 — smaž doklad <id>
def rfq_doklad_cmd(rest: str) -> dict:
    raw = (rest or "").strip()
    up = raw.upper()

    def _row(*vals):
        return {"ok": True, "columns": None, "rows": [list(vals)]}

    def _out(columns, rows):
        return {"ok": True, "columns": columns, "rows": rows}

    def _err(msg):
        return {"ok": True, "columns": ["chyba"], "rows": [[str(msg)]]}

    try:
        if up.startswith("DIAG"):
            sql = (
                "DECLARE @IDENT int, @Message nvarchar(255) "
                "EXEC [dbo].[EC_GenVydanouPoptavku] @IDENT = @IDENT OUTPUT, @Message = @Message OUTPUT "
                "SELECT @IDENT AS IDENT, @Message AS Message"
            )
            res = _ec_raw(sql)
            keys = list(res.keys()) if isinstance(res, dict) else []
            rows = res.get("rows") if isinstance(res, dict) else None
            return _out(
                ["pole", "hodnota"],
                [
                    ["ok", str(res.get("ok"))],
                    ["keys", ", ".join(keys)],
                    ["rows_count", str(len(rows) if isinstance(rows, list) else rows)],
                    ["rows[0]", (json.dumps(rows[0], ensure_ascii=False)[:200] if rows else "-")],
                    ["message", str(res.get("message") or res.get("error") or "-")[:200]],
                ],
            )

        if up.startswith("PROBE") or raw == "":
            p = probe()
            if not p.get("ok"):
                return _err("PROBE selhal (guard/write path): %s" % p.get("error"))
            r0 = (p.get("rows") or [{}])[0]
            return _out(
                ["probe", "výsledek"],
                [["MCP write path OK ✓ (batch DECLARE/SELECT prošel)",
                  "probe=%s ver=%s" % (r0.get("probe"), (r0.get("ver") or "")[:40])]],
            )

        if up.startswith("TEST"):
            g = gen_vydana_poptavka()
            if not g.get("ok"):
                return _err("GEN selhal: %s" % g.get("error"))
            did = g.get("ident")
            hdr = _header(did)
            s = smaz_vydana_poptavka(did)
            return _out(
                ["krok", "hodnota"],
                [
                    ["1) vygenerováno", "ID=%s  doklad=%s  msg=%s" % (did, hdr.get("doklad"), g.get("message"))],
                    ["2) hlavička", "rada=%s porcis=%s autor=%s" % (hdr.get("RadaDokladu"), hdr.get("PoradoveCislo"), hdr.get("Autor"))],
                    ["3) smazáno", ("OK ✓ (beze stopy) msg=%s" % s.get("message")) if s.get("ok") else ("SMAZ selhal: %s" % s.get("error"))],
                ],
            )

        if up.startswith("KONTAKTY"):
            org = raw[len("KONTAKTY"):].strip()
            if not org:
                return _err("použij: @@RFQDOKLAD KONTAKTY <cisloOrg>")
            ks = find_org_contacts(org)
            if not ks:
                return _out(["dodavatel org=%s" % org, "kontakt"], [["(žádné aktivní kontaktní osoby)", ""]])
            rows = [[k.get("osoba"), "%s | %s | %s" % (k.get("funkce") or "-", k.get("email") or "-", k.get("tel") or "-")] for k in ks[:40]]
            return _out(["osoba (org=%s)" % org, "funkce | email | tel"], rows)

        if up.startswith("DIR"):
            doklad = raw[3:].strip()
            if not doklad:
                return _err("použij: @@RFQDOKLAD DIR <doklad>  (např. EVP260231)")
            r = list_poptavka_dir(doklad)
            if not r.get("ok"):
                return _err("přístup do %s\\%s selhal: %s" % (_POPTAVKY_ROOT, doklad, r.get("error") or r))
            items = r.get("items") or r.get("entries") or r.get("files") or []
            if not items:
                return _out(["adresář", "obsah"], [["%s\\%s" % (_POPTAVKY_ROOT, doklad), "(prázdný / bez souborů)"]])
            rows = []
            for it in items[:50]:
                if isinstance(it, dict):
                    rows.append([it.get("name") or it.get("path") or str(it),
                                 str(it.get("size", it.get("type", "")))])
                else:
                    rows.append([str(it), ""])
            return _out(["soubor (%s\\%s)" % (_POPTAVKY_ROOT, doklad), "velikost/typ"], rows)

        if up.startswith("FILL"):
            import datetime as _dt
            g = gen_vydana_poptavka()
            if not g.get("ok"):
                return _err("GEN selhal: %s" % g.get("error"))
            did = g.get("ident")
            termin = (_dt.date.today() + _dt.timedelta(days=14)).isoformat()
            uh = update_poptavka_header(did, cislo_org="252", termin_dat=termin, mena="EUR")
            ue = update_poptavka_ext(did, "TEST poptávka STRATEGIE — díly rozváděče (Claude ID23)")
            r = read_poptavka(did)
            steps = []
            steps.append(["1) vygenerováno", "ID=%s  doklad=%s" % (did, r.get("doklad"))])
            steps.append(["2) header UPDATE", "OK ✓" if uh.get("ok") else ("SELHAL: %s" % uh.get("error"))])
            steps.append(["3) EXT název UPDATE", "OK ✓" if ue.get("ok") else ("SELHAL: %s" % ue.get("error"))])
            steps.append(["4) čtení zpět — dodavatel", "%s (CisloOrg=%s)" % (r.get("firma"), r.get("CisloOrg"))])
            steps.append(["4) čtení zpět — název poptávky", str(r.get("nazev_poptavky"))])
            steps.append(["4) čtení zpět — termín / měna", "%s / %s" % (r.get("termin"), r.get("Mena"))])
            steps.append(["→ úklid", "@@RFQDOKLAD SMAZ %s" % did])
            return _out(["krok", "hodnota"], steps)

        if up.startswith("GEN"):
            g = gen_vydana_poptavka()
            if not g.get("ok"):
                return _err("GEN selhal: %s" % g.get("error"))
            hdr = _header(g.get("ident"))
            return _out(["ID", "doklad", "rada", "porcis", "message"],
                        [[g.get("ident"), hdr.get("doklad"), hdr.get("RadaDokladu"),
                          hdr.get("PoradoveCislo"), g.get("message")]])

        if up.startswith("SMAZ"):
            arg = raw[4:].strip()
            if not arg.isdigit():
                return _err("použij: @@RFQDOKLAD SMAZ <id>")
            s = smaz_vydana_poptavka(int(arg))
            return _err(("smazáno ✓ msg=%s" % s.get("message")) if s.get("ok") else ("SMAZ selhal: %s" % s.get("error")))

        return _err("neznámý pod-příkaz. PROBE | TEST | GEN | SMAZ <id>")
    except Exception as e:
        return _err("neočekávaná chyba: %s: %s" % (type(e).__name__, e))
