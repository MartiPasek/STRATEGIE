"""
Přijatá poptávka (od zákazníka, řada 900) — TEST paralelní engine. Claude ID24, 19. 7. 2026.

Zrcadlo rfq_doklad.py / rfq_draft.py, ale pro DRUHOU stranu trychtýře: zákazník
poptává NÁS (Anfrage) → založíme přijatou poptávku (EP) → odpovíme konceptem →
vygenerujeme kalkulaci + nabídku → doceníme. Na tomhle enginu se tok učíme NAOSTRO,
ale bezpečně vedle produkce: VŠECHNY popisy / texty / předměty e-mailů nesou prefix
"TEST" (pokyn Marti 19. 7.). E-maily jen jako KONCEPTY (doktrína návrh→schválení).

Procedury (DB_EC — z definic + Marti):
  založení:  EXEC dbo.EC_GenPoptavku @Uzivatel, @ErrorCode OUT, @IDENT OUT, @Message OUT
             (proc si @Uzivatel přepíše na SUSER_SNAME() → doklad má CisloZam MCP loginu;
              řešitele/organizaci/kontakt/popisy doplníme UPDATE-em po vygenerování)
  kalk+nab:  EXEC dbo.EC_GenKalkulaciANabidku @ID_Poptavky, @IDENT OUT (=NABÍDKA), @MESSAGE OUT
             → nabídka EN (řada 910) + kalkulace EK (EC_KalkulaceHlav) + vazby (poptávka→
               kalkulace→nabídka) + přenos položek (BOM) + na poptávce Splneno=1
  smazání:   EXEC dbo.EC_SmazPrijatouPoptavku @IDDoklad, @Message OUT   (guard: jen řada 900)

Zápis do DB_EC jde přes EUROSOFT MCP (strategie_query_raw), NE přes read-only most.
Předloha polí = produkční EP26306 (ABSAUGWERK AB12600504 / P00881, Flex 11 kW).
"""
from __future__ import annotations

import json

from core.logging import get_logger

logger = get_logger("erp.prijata_poptavka")

# ── předloha TEST poptávky (dle produkčního EP26306 / AB12600504) ────────────
TEST_ORG = 10077          # ABSAUGWERK GmbH (TabCisOrg.CisloOrg)
TEST_RESITEL = 24         # Eliška Kolářová (TabCisZam.Cislo)
TEST_STRED = "001"
TEST_KONTAKT = 2852       # Regele Georg (TabCisKOs.ID)
TEST_OBLAST = "Rozvaděč"
TEST_JAZYK = "DE"
TEST_OZN = "TEST AB12600504 / P00881, Flex 11 kW"
TEST_POPIS = "TEST AB12600504 / P00881, Flex 11 kW"
TEST_KONTAKT_EMAIL_FALLBACK = "g.regele@absaugwerk.de"
ELISKA_USER = 34          # STRATEGIE users.id (schránka pro koncept)


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


# ── marker v st. (zachycení @IDENT přes write-režim MCP, který zahazuje result-sety) ──
def _ensure_marker() -> None:
    _ec_raw(
        "IF OBJECT_ID('st.pp_gen_marker') IS NULL "
        "CREATE TABLE st.pp_gen_marker("
        "id int IDENTITY(1,1) PRIMARY KEY, nonce nvarchar(64), ident int, "
        "msg nvarchar(255), created datetime DEFAULT GETDATE())"
    )


def _gen_via_marker(exec_sql_tpl: str) -> dict:
    """Spustí write batch, který na konci zapíše @IDENT+@Message do markeru, a přečte je zpět."""
    import uuid
    _ensure_marker()
    nonce = uuid.uuid4().hex
    sql = exec_sql_tpl + (
        " INSERT INTO st.pp_gen_marker(nonce, ident, msg) VALUES(N'%s', @IDENT, @Message)" % nonce
    )
    res = _ec_raw(sql)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    rb = _ec_raw("SELECT TOP 1 ident, msg FROM st.pp_gen_marker WHERE nonce=N'%s' ORDER BY id DESC" % nonce)
    rows = rb.get("rows") or []
    if not rows:
        return {"ok": False, "error": "marker nevrátil IDENT (nonce=%s)" % nonce}
    r = rows[0]
    ident = _int(r.get("ident"))
    if not ident:
        return {"ok": False, "error": "IDENT prázdný — proc doklad nezaložila. msg=%s" % r.get("msg")}
    return {"ok": True, "ident": ident, "message": r.get("msg"), "nonce": nonce}


# ── 1) založení přijaté poptávky (EC_GenPoptavku) ────────────────────────────
def gen_prijata_poptavka() -> dict:
    return _gen_via_marker(
        "DECLARE @IDENT int, @ErrorCode int, @Message nvarchar(255) "
        "EXEC [dbo].[EC_GenPoptavku] @Uzivatel = %d, @ErrorCode = @ErrorCode OUTPUT, "
        "@IDENT = @IDENT OUTPUT, @Message = @Message OUTPUT" % TEST_RESITEL
    )


# ── 2) doplnění polí (TEST) dle předlohy EP26306 ─────────────────────────────
def fill_prijata_poptavka(doklad_id: int) -> dict:
    did = int(doklad_id)
    h = _ec_raw(
        "UPDATE TabDokladyZbozi SET CisloOrg=%d, CisloZam=%d, StredNaklad=%s, KontaktOsoba=%d "
        "WHERE ID=%d" % (TEST_ORG, TEST_RESITEL, _q(TEST_STRED), TEST_KONTAKT, did)
    )
    if not h.get("ok"):
        return {"ok": False, "error": "header UPDATE: %s" % (h.get("message") or h.get("error"))}
    e = _ec_raw(
        "IF EXISTS(SELECT 1 FROM TabDokladyZbozi_EXT WHERE ID=%d) "
        "UPDATE TabDokladyZbozi_EXT SET _OznPrjZakaznik=%s, _PopisPrjZakaznik=%s, _Oblast=%s, _Jazyk=%s WHERE ID=%d "
        "ELSE INSERT INTO TabDokladyZbozi_EXT(ID,_OznPrjZakaznik,_PopisPrjZakaznik,_Oblast,_Jazyk) VALUES(%d,%s,%s,%s,%s)"
        % (did, _q(TEST_OZN), _q(TEST_POPIS), _q(TEST_OBLAST), _q(TEST_JAZYK), did,
           did, _q(TEST_OZN), _q(TEST_POPIS), _q(TEST_OBLAST), _q(TEST_JAZYK))
    )
    if not e.get("ok"):
        return {"ok": False, "error": "EXT UPDATE: %s" % (e.get("message") or e.get("error"))}
    return {"ok": True}


def read_prijata_poptavka(doklad_id: int) -> dict:
    did = int(doklad_id)
    sql = (
        "SELECT dbo.EC_GetDoklad(d.ID) AS doklad, d.RadaDokladu, d.PoradoveCislo, d.CisloOrg, "
        "o.Nazev AS org, d.CisloZam, z.LoginID AS resitel, d.StredNaklad, d.KontaktOsoba, "
        "(ko.Prijmeni+' '+ISNULL(ko.Jmeno,'')) AS kontakt, d.Splneno, "
        "dbo.EC_GetDoklad(d.NavaznyDoklad) AS navazny, e._OznPrjZakaznik AS ozn, "
        "e._PopisPrjZakaznik AS popis, e._Oblast AS oblast, e._Jazyk AS jazyk "
        "FROM TabDokladyZbozi d "
        "LEFT JOIN TabCisOrg o ON d.CisloOrg=o.CisloOrg "
        "LEFT JOIN TabCisZam z ON d.CisloZam=z.Cislo "
        "LEFT JOIN TabCisKOs ko ON d.KontaktOsoba=ko.ID "
        "LEFT JOIN TabDokladyZbozi_EXT e ON e.ID=d.ID WHERE d.ID=%d" % did
    )
    res = _ec_raw(sql)
    rows = res.get("rows") or []
    return rows[0] if rows else {}


# ── 3) koncept odpovědi zákazníkovi (TEST v předmětu; NEodesílá) ─────────────
def _kontakt_email(ko_id: int) -> str | None:
    r = _ec_raw(
        "SELECT TOP 1 Spojeni FROM TabKontakty WHERE IDCisKOs=%d AND Druh=6 "
        "AND ISNULL(Prednastaveno,0)=1 AND IDVztahKOsOrg IS NULL" % int(ko_id)
    )
    rows = r.get("rows") or []
    return (rows[0].get("Spojeni") if rows else None) or None


def reply_koncept(doklad_id: int) -> dict:
    """Uloží TEST koncept odpovědi na poptávku do Eliščiny schránky (Koncepty). NEODESÍLÁ."""
    from modules.erp.api.rfq_draft import create_email_draft
    hdr = read_prijata_poptavka(doklad_id)
    doklad = hdr.get("doklad") or ("ID%s" % doklad_id)
    ozn = hdr.get("ozn") or TEST_OZN
    to_email = _kontakt_email(hdr.get("KontaktOsoba") or TEST_KONTAKT) or TEST_KONTAKT_EMAIL_FALLBACK
    subject = "TEST RE: Anforderung Schaltschrank AB12600504 / P00881 — Angebot in Bearbeitung (%s)" % doklad
    body = (
        "TEST — testovací koncept (paralelní engine STRATEGIE, Claude). Needeslat produkčně.\n\n"
        "Sehr geehrter Herr Regele,\n\n"
        "vielen Dank für Ihre Anfrage AB12600504 / P00881 (Steuerung Flex 11 kW). "
        "Wir haben Ihre Anfrage erhalten und erstellen Ihnen dazu ein Angebot. "
        "Das Angebot lassen wir Ihnen in Kürze zukommen.\n\n"
        "Mit freundlichen Grüßen\n"
        "Eliška Kolářová\n"
        "EUROSOFT-Control s.r.o.\n\n"
        "-- interní ref.: %s / %s --" % (doklad, ozn)
    )
    res = create_email_draft(
        to=to_email, subject=subject, body=body, user_id=ELISKA_USER, from_identity="user",
    )
    return {"ok": True, "to": to_email, "subject": subject,
            "folder": res.get("folder"), "sender": res.get("sender")}


# ── 4) generování kalkulace + nabídky (EC_GenKalkulaciANabidku) ──────────────
def gen_kalkulace_nabidka(id_poptavky: int) -> dict:
    # EC_GenKalkulaciANabidku končí voláním EC_MenuStrom_SetSoudecek (přepnutí UI stromu
    # operátora na novou nabídku), které v headless MCP kontextu padá (sloupec 'User' = NULL).
    # Obalíme TRY/CATCH + SET XACT_ABORT OFF → constraint chyba jen ukončí ten statement,
    # transakce zůstane commitnutelná, jádro (nabídka + kalkulace + vazby + přenos BOM +
    # Splneno=1) zůstane. ID nabídky NEbereme z @IDENT OUTPUT (na chybě se nevrátí), ale
    # z poptávka.NavaznyDoklad, který proc nastaví PŘED padajícím krokem.
    import uuid
    _ensure_marker()
    nonce = uuid.uuid4().hex
    pid = int(id_poptavky)
    sql = (
        "DECLARE @IDENT int, @Message nvarchar(255), @nab int "
        "SET XACT_ABORT OFF "
        "BEGIN TRY "
        "EXEC [dbo].[EC_GenKalkulaciANabidku] @ID_Poptavky=%d, @IDENT=@IDENT OUTPUT, @MESSAGE=@Message OUTPUT "
        "END TRY "
        "BEGIN CATCH "
        "SET @Message = N'SetSoudecek preskocen (headless): ' + LEFT(ERROR_MESSAGE(),110) "
        "END CATCH "
        "IF XACT_STATE() = -1 ROLLBACK ELSE WHILE @@TRANCOUNT > 0 COMMIT "
        "SELECT @nab = NavaznyDoklad FROM TabDokladyZbozi WHERE ID=%d "
        "INSERT INTO st.pp_gen_marker(nonce, ident, msg) VALUES(N'%s', @nab, @Message)"
        % (pid, pid, nonce)
    )
    res = _ec_raw(sql)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    rb = _ec_raw("SELECT TOP 1 ident, msg FROM st.pp_gen_marker WHERE nonce=N'%s' ORDER BY id DESC" % nonce)
    rows = rb.get("rows") or []
    nab_id = _int(rows[0].get("ident")) if rows else None
    msg = rows[0].get("msg") if rows else None
    if not nab_id:
        return {"ok": False, "error": "nabídka nevznikla (NavaznyDoklad prázdný → rollback). msg=%s" % msg}
    info = _ec_raw(
        "SELECT dbo.EC_GetDoklad(%d) AS nabidka, k.CisloKalkulace AS kalkulace, "
        "(SELECT COUNT(*) FROM TabPohybyZbozi p WHERE p.IDDoklad=%d) AS polozek_nab "
        "FROM EC_KalkulaceHlav k WHERE k.IDDoklad=%d" % (nab_id, nab_id, nab_id)
    )
    rows2 = info.get("rows") or []
    r0 = rows2[0] if rows2 else {}
    return {"ok": True, "nabidka_id": nab_id, "nabidka": r0.get("nabidka"),
            "kalkulace": r0.get("kalkulace"), "polozek": r0.get("polozek_nab"), "message": msg}


# ── 5) smazání (úklid TEST) — guard řada 900 ─────────────────────────────────
def smaz_prijata_poptavka(doklad_id: int) -> dict:
    did = int(doklad_id)
    chk = _ec_raw("SELECT RadaDokladu AS r FROM TabDokladyZbozi WHERE ID=%d" % did)
    crows = chk.get("rows") or []
    if not crows:
        return {"ok": False, "error": "doklad ID=%d neexistuje" % did}
    rada = str((crows[0] or {}).get("r") or "").strip()
    if rada != "900":
        return {"ok": False, "error": "ID=%d NENÍ přijatá poptávka (řada=%s) — mazání odmítnuto" % (did, rada)}
    res = _ec_raw(
        "DECLARE @Message nvarchar(200) DECLARE @ID int = %d "
        "EXEC EC_SmazPrijatouPoptavku @IDDoklad=@ID, @Message=@Message OUTPUT "
        "SELECT @Message AS Message" % did
    )
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    rows = res.get("rows") or []
    return {"ok": True, "message": (rows[0].get("Message") if rows else None)}


# ── @@ dispatch ──────────────────────────────────────────────────────────────
#   @@PP GEN            — založí TEST přijatou poptávku (EP), vrátí ID
#   @@PP FILL <id>      — doplní pole dle předlohy EP26306 (org/řešitel/kontakt/oblast + TEST popisy)
#   @@PP SHOW <id>      — čtení dokladu zpět
#   @@PP REPLY <id>     — TEST koncept odpovědi zákazníkovi (do Eliščiných Konceptů, NEodesílá)
#   @@PP KALK <id>      — EC_GenKalkulaciANabidku → nabídka EN + kalkulace EK
#   @@PP SMAZ <id>      — smazání (guard řada 900)
def prijata_poptavka_cmd(rest: str) -> dict:
    raw = (rest or "").strip()
    up = raw.upper()

    def _out(columns, rows):
        return {"ok": True, "columns": columns, "rows": rows}

    def _err(msg):
        return {"ok": True, "columns": ["chyba"], "rows": [[str(msg)]]}

    def _idarg(prefix):
        a = raw[len(prefix):].strip()
        return int(a) if a.isdigit() else None

    try:
        if up.startswith("GEN"):
            g = gen_prijata_poptavka()
            if not g.get("ok"):
                return _err("GEN selhal: %s" % g.get("error"))
            hdr = read_prijata_poptavka(g.get("ident"))
            return _out(["ID", "doklad", "rada", "porcis", "message"],
                        [[g.get("ident"), hdr.get("doklad"), hdr.get("RadaDokladu"),
                          hdr.get("PoradoveCislo"), g.get("message") or "OK"]])

        if up.startswith("FILL"):
            did = _idarg("FILL")
            if not did:
                return _err("použij: @@PP FILL <id>")
            f = fill_prijata_poptavka(did)
            if not f.get("ok"):
                return _err(f.get("error"))
            r = read_prijata_poptavka(did)
            return _out(["pole", "hodnota"], [
                ["doklad", str(r.get("doklad"))],
                ["organizace", "%s (CisloOrg=%s)" % (r.get("org"), r.get("CisloOrg"))],
                ["řešitel", "%s (CisloZam=%s)" % (r.get("resitel"), r.get("CisloZam"))],
                ["kontakt", "%s (ID=%s)" % (r.get("kontakt"), r.get("KontaktOsoba"))],
                ["označení (TEST)", str(r.get("ozn"))],
                ["oblast / jazyk", "%s / %s" % (r.get("oblast"), r.get("jazyk"))],
            ])

        if up.startswith("SHOW"):
            did = _idarg("SHOW")
            if not did:
                return _err("použij: @@PP SHOW <id>")
            r = read_prijata_poptavka(did)
            if not r:
                return _err("doklad ID=%d nenalezen" % did)
            return _out(["pole", "hodnota"], [
                ["doklad", str(r.get("doklad"))],
                ["organizace", "%s (%s)" % (r.get("org"), r.get("CisloOrg"))],
                ["řešitel", str(r.get("resitel"))],
                ["kontakt", str(r.get("kontakt"))],
                ["označení", str(r.get("ozn"))],
                ["splněno / navazný", "%s / %s" % (r.get("Splneno"), r.get("navazny") or "-")],
                ["oblast / jazyk", "%s / %s" % (r.get("oblast"), r.get("jazyk"))],
            ])

        if up.startswith("REPLY"):
            did = _idarg("REPLY")
            if not did:
                return _err("použij: @@PP REPLY <id>")
            rp = reply_koncept(did)
            return _out(["výsledek", "hodnota"], [
                ["TEST koncept uložen ✓ (NEodesláno)", rp.get("folder")],
                ["schránka", rp.get("sender")],
                ["příjemce", rp.get("to")],
                ["předmět", rp.get("subject")],
            ])

        if up.startswith("KALK"):
            did = _idarg("KALK")
            if not did:
                return _err("použij: @@PP KALK <id>")
            k = gen_kalkulace_nabidka(did)
            if not k.get("ok"):
                return _err("KALK selhal: %s" % k.get("error"))
            return _out(["výsledek", "hodnota"], [
                ["nabídka vygenerována ✓", "%s (ID=%s)" % (k.get("nabidka"), k.get("nabidka_id"))],
                ["kalkulace", str(k.get("kalkulace"))],
                ["položek přeneseno do nabídky", str(k.get("polozek"))],
                ["message", str(k.get("message") or "OK")],
            ])

        if up.startswith("SMAZ"):
            did = _idarg("SMAZ")
            if not did:
                return _err("použij: @@PP SMAZ <id>")
            s = smaz_prijata_poptavka(did)
            return _err(("smazáno ✓ msg=%s" % s.get("message")) if s.get("ok")
                        else ("SMAZ selhal: %s" % s.get("error")))

        return _err("neznámý pod-příkaz. GEN | FILL <id> | SHOW <id> | REPLY <id> | KALK <id> | SMAZ <id>")
    except Exception as e:
        return _err("neočekávaná chyba: %s: %s" % (type(e).__name__, e))
