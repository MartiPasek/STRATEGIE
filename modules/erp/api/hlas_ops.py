"""Hlas engine — app-level operace (zapis pres @@HLAS z mostu).
Integrita mekkych odkazu (entita_id/graf_id/domain_key) se hlida ZDE na app
vrstve — schema hlas nema cross-schema FK do g2007 (volba B, Marti 22.7.2026).
Obsahuje i normalizaci cisel/symbolu do cestiny (hlavni paka verohodnosti)."""
import json as _json
import re as _re
from sqlalchemy import text as _t

# ── Cesky prevod cisel na slova (0..999999) ────────────────────────────────
_JED = ["nula", "jedna", "dva", "tři", "čtyři", "pět", "šest", "sedm", "osm",
        "devět", "deset", "jedenáct", "dvanáct", "třináct", "čtrnáct", "patnáct",
        "šestnáct", "sedmnáct", "osmnáct", "devatenáct"]
_DES = ["", "", "dvacet", "třicet", "čtyřicet", "padesát", "šedesát",
        "sedmdesát", "osmdesát", "devadesát"]


def _pod_tisic(n):
    s = []
    st, zb = n // 100, n % 100
    if st == 1:
        s.append("sto")
    elif st == 2:
        s.append("dvě stě")
    elif st in (3, 4):
        s.append(_JED[st] + " sta")
    elif st >= 5:
        s.append(_JED[st] + " set")
    if zb:
        if zb < 20:
            s.append(_JED[zb])
        else:
            d, j = zb // 10, zb % 10
            s.append(_DES[d] + (" " + _JED[j] if j else ""))
    return " ".join(s)


def _cislo_slovy(n):
    n = int(n)
    if n == 0:
        return "nula"
    if n < 0:
        return "mínus " + _cislo_slovy(-n)
    s = []
    tis, zb = n // 1000, n % 1000
    if tis == 1:
        s.append("tisíc")
    elif tis in (2, 3, 4):
        s.append(_pod_tisic(tis) + " tisíce")
    elif tis >= 5:
        s.append(_pod_tisic(tis) + " tisíc")
    if zb:
        s.append(_pod_tisic(zb))
    return " ".join(s)


def _prevod_cisla_v_textu(text):
    def repl_dec(m):
        return _cislo_slovy(int(m.group(1))) + " celá " + _cislo_slovy(int(m.group(2)))
    text = _re.sub(r"(\d+),(\d+)", repl_dec, text)

    def repl_int(m):
        tok = m.group(0)
        if len(tok) > 1 and tok[0] == "0":
            return " ".join(_JED[int(c)] for c in tok)  # kod s vodici nulou -> po cislicich
        n = int(tok)
        if n > 999999:
            return " ".join(_JED[int(c)] for c in tok)   # moc velke -> po cislicich
        return _cislo_slovy(n)
    return _re.sub(r"\d+", repl_int, text)


def _one(sg, sql, **p):
    return sg.execute(_t(sql), p).scalar()


# ── Normalizace textu (pravidla z hlas.vyslovnost + prevod cisel) ─────────
def normalizuj(text=None, tenant_id=None, scope_ref=None):
    from core.database import get_session
    if text is None:
        return {"ok": False, "error": "text je povinny"}
    sg = get_session()
    try:
        rows = sg.execute(_t(
            "SELECT rezim, vzor, nahrada FROM hlas.vyslovnost "
            "WHERE stav='aktivni' AND (tenant_id IS NULL OR tenant_id=:t) AND ("
            "  scope='global' OR (scope IN ('domena','kanal') AND scope_ref=:sr)) "
            "ORDER BY priorita, id"),
            {"t": tenant_id, "sr": scope_ref}).fetchall()
    finally:
        sg.close()
    out = text
    for rezim, vzor, nahrada in rows:
        if rezim == "regex":
            try:
                out = _re.sub(vzor, nahrada, out)
            except _re.error:
                pass
        else:
            out = out.replace(vzor, nahrada)
    out = _prevod_cisla_v_textu(out)
    out = _re.sub(r"\s+", " ", out).strip()
    return {"ok": True, "columns": ["vstup", "vystup"], "rows": [[text, out]]}


# ── Sprava pravidel vyslovnosti ────────────────────────────────────────────
def vyslovnost_add(typ=None, vzor=None, nahrada=None, rezim="alias", scope="global",
                   scope_ref=None, priorita=100, tenant_id=None, poznamka=None):
    from core.database import get_session
    if not typ or vzor is None or nahrada is None:
        return {"ok": False, "error": "typ, vzor, nahrada jsou povinne"}
    sg = get_session()
    try:
        nid = sg.execute(_t(
            "INSERT INTO hlas.vyslovnost (tenant_id, scope, scope_ref, typ, rezim, vzor, "
            "nahrada, priorita, poznamka) VALUES (:t,:sc,:sr,:ty,:rz,:vz,:na,:pr,:po) "
            "RETURNING id"),
            {"t": tenant_id, "sc": scope, "sr": scope_ref, "ty": typ, "rz": rezim,
             "vz": vzor, "na": nahrada, "pr": priorita, "po": poznamka}).scalar()
        sg.commit()
        return {"ok": True, "id": nid}
    except Exception as e:
        try:
            sg.rollback()
        except Exception:
            pass
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:300])}
    finally:
        sg.close()


_DEFAULT_PRAVIDLA = [
    # (typ, rezim, vzor, nahrada, priorita)
    ("symbol", "alias", "×", " krát ", 50),
    ("symbol", "alias", "%", " procent", 50),
    ("symbol", "alias", "€", " eur", 50),
    ("symbol", "alias", "+", " plus ", 50),
    ("symbol", "alias", "&", " a ", 50),
    ("symbol", "regex", r"(?<=\d)\s*/\s*(?=\d)", " lomeno ", 40),
    ("symbol", "regex", r"(?<=\d)\s*-\s*(?=\d)", " pomlčka ", 40),
    ("zkratka", "regex", r"\bč\.\s*(?=\d)", "číslo ", 30),
]


def vyslovnost_seed_default():
    from core.database import get_session
    sg = get_session()
    vlozeno, preskoceno = 0, 0
    try:
        for typ, rezim, vzor, nahrada, priorita in _DEFAULT_PRAVIDLA:
            ex = sg.execute(_t(
                "SELECT 1 FROM hlas.vyslovnost WHERE scope='global' AND vzor=:v AND typ=:ty"),
                {"v": vzor, "ty": typ}).scalar()
            if ex:
                preskoceno += 1
                continue
            sg.execute(_t(
                "INSERT INTO hlas.vyslovnost (scope, typ, rezim, vzor, nahrada, priorita, poznamka) "
                "VALUES ('global',:ty,:rz,:vz,:na,:pr,'seed default 22.7.')"),
                {"ty": typ, "rz": rezim, "vz": vzor, "na": nahrada, "pr": priorita})
            vlozeno += 1
        sg.commit()
        return {"ok": True, "columns": ["vlozeno", "preskoceno"], "rows": [[vlozeno, preskoceno]]}
    except Exception as e:
        try:
            sg.rollback()
        except Exception:
            pass
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:300])}
    finally:
        sg.close()


# ── Kanal ──────────────────────────────────────────────────────────────────
def hlas_kanal_upsert(tenant_id=None, kod=None, nazev=None, typ="text", entita_id=None,
                      domain_key=None, graf_id=None, config=None, stav="navrh", poradi=0):
    from core.database import get_session
    if not tenant_id or not kod:
        return {"ok": False, "error": "tenant_id a kod jsou povinne"}
    if typ not in ("text", "hlas", "telefon"):
        return {"ok": False, "error": "typ musi byt text|hlas|telefon"}
    sg = get_session()
    try:
        if entita_id is not None:
            if not _one(sg, "SELECT 1 FROM g2007.entita WHERE id=:i", i=entita_id):
                return {"ok": False, "error": "entita_id %s neexistuje v g2007.entita" % entita_id}
        if graf_id is not None:
            if not _one(sg, "SELECT 1 FROM g2007.graf WHERE id=:i", i=graf_id):
                return {"ok": False, "error": "graf_id %s neexistuje v g2007.graf" % graf_id}
        if domain_key:
            if not _one(sg, "SELECT 1 FROM tenant.domain_env WHERE tenant_id=:t AND domain_key=:d",
                        t=tenant_id, d=domain_key):
                return {"ok": False, "error": "domain_key '%s' neexistuje v tenant.domain_env (tenant %s)"
                        % (domain_key, tenant_id)}
        cfg = _json.dumps(config or {})
        row = sg.execute(_t(
            "INSERT INTO hlas.kanal (tenant_id, firma, kod, nazev, typ, entita_id, domain_key, "
            "graf_id, config, stav, poradi) "
            "VALUES (:tenant_id, NULL, :kod, :nazev, :typ, :entita_id, :domain_key, :graf_id, "
            "CAST(:config AS jsonb), :stav, :poradi) "
            "ON CONFLICT (tenant_id, kod) DO UPDATE SET "
            "nazev=EXCLUDED.nazev, typ=EXCLUDED.typ, entita_id=EXCLUDED.entita_id, "
            "domain_key=EXCLUDED.domain_key, graf_id=EXCLUDED.graf_id, config=EXCLUDED.config, "
            "stav=EXCLUDED.stav, poradi=EXCLUDED.poradi, updated_at=now() "
            "RETURNING id, (xmax=0) AS inserted"),
            {"tenant_id": tenant_id, "kod": kod, "nazev": nazev, "typ": typ,
             "entita_id": entita_id, "domain_key": domain_key, "graf_id": graf_id,
             "config": cfg, "stav": stav, "poradi": poradi}).first()
        sg.commit()
        return {"ok": True, "id": row[0], "akce": "insert" if row[1] else "update", "kod": kod}
    except Exception as e:
        try:
            sg.rollback()
        except Exception:
            pass
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:300])}
    finally:
        sg.close()


def dispatch(payload):
    if not isinstance(payload, dict):
        return {"ok": False, "error": "payload musi byt JSON objekt"}
    op = (payload.get("op") or "").strip()
    args = {k: v for k, v in payload.items() if k != "op"}
    if op == "kanal_upsert":
        return hlas_kanal_upsert(**args)
    if op == "normalizuj":
        return normalizuj(**args)
    if op == "vyslovnost_add":
        return vyslovnost_add(**args)
    if op == "vyslovnost_seed_default":
        return vyslovnost_seed_default()
    return {"ok": False, "error": "neznamy op '%s' (znam: kanal_upsert, normalizuj, vyslovnost_add, vyslovnost_seed_default)" % op}
