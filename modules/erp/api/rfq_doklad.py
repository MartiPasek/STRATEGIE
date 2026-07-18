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


# ── UPDATE běžných fieldů hlavičky (povoleno napřímo) ───────────────────────
def update_poptavka_fields(
    doklad_id: int,
    cislo_org: str | None = None,
    popis: str | None = None,
    text1: str | None = None,
    poznamka: str | None = None,
    mena: str | None = None,
) -> dict:
    sets = []
    if cislo_org is not None:
        sets.append("CisloOrg = %s" % _q(cislo_org))
    if popis is not None:
        sets.append("PopisDodavky = %s" % _q(popis))
    if text1 is not None:
        sets.append("Text1 = %s" % _q(text1))
    if poznamka is not None:
        sets.append("Poznamka = %s" % _q(poznamka))
    if mena is not None:
        sets.append("Mena = %s" % _q(mena))
    if not sets:
        return {"ok": False, "error": "žádné pole k updatu"}
    sql = "UPDATE TabDokladyZbozi SET %s WHERE ID = %d" % (", ".join(sets), int(doklad_id))
    res = _ec_raw(sql)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("message") or res.get("error")}
    return {"ok": True}


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
