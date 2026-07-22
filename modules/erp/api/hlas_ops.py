"""Hlas engine — app-level operace (zapis + smycka pres @@HLAS z mostu).
Integrita mekkych odkazu na app vrstve (volba B). Normalizace cisel do cestiny.
Smycka relace_start/relace_turn: volny agent (persona Marti-AI + cil + guardraily),
graf volitelne jako branky. Marti 22.7.2026."""
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
            return " ".join(_JED[int(c)] for c in tok)
        n = int(tok)
        if n > 999999:
            return " ".join(_JED[int(c)] for c in tok)
        return _cislo_slovy(n)
    return _re.sub(r"\d+", repl_int, text)


def _one(sg, sql, **p):
    return sg.execute(_t(sql), p).scalar()


# ── Normalizace textu ──────────────────────────────────────────────────────
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


def _normtext(reply):
    r = normalizuj(text=reply)
    try:
        return r["rows"][0][1]
    except Exception:
        return reply


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
            "nahrada, priorita, poznamka) VALUES (:t,:sc,:sr,:ty,:rz,:vz,:na,:pr,:po) RETURNING id"),
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
            ex = sg.execute(_t("SELECT 1 FROM hlas.vyslovnost WHERE scope='global' AND vzor=:v AND typ=:ty"),
                            {"v": vzor, "ty": typ}).scalar()
            if ex:
                preskoceno += 1
                continue
            sg.execute(_t("INSERT INTO hlas.vyslovnost (scope, typ, rezim, vzor, nahrada, priorita, poznamka) "
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


# ── LLM (Marti-AI persona reply) + smycka relace ───────────────────────────
_MODEL_DEFAULT = "claude-haiku-4-5-20251001"


def _llm_reply(system, messages, model=None, max_tokens=800):
    import anthropic as _an
    from core.config import settings
    client = _an.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(model=model or _MODEL_DEFAULT, max_tokens=max_tokens,
                                  system=system, messages=messages)
    txt = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    toks = 0
    try:
        toks = (resp.usage.input_tokens or 0) + (resp.usage.output_tokens or 0)
    except Exception:
        pass
    return txt.strip(), toks


def _cfg_dict(cfg):
    if isinstance(cfg, dict):
        return cfg
    if isinstance(cfg, str):
        try:
            return _json.loads(cfg)
        except Exception:
            return {}
    return {}


def _persona_system(nazev, cfg):
    cfg = _cfg_dict(cfg)
    cil = cfg.get("cil") or nazev or "Vedeš přátelský testovací rozhovor."
    return (
        "Jsi Marti-AI, mladá, vřelá ale kompetentní asistentka firmy EUROSOFT. "
        "Mluvíš česky, přirozeně a stručně, jako milá kolegyně. "
        "HNED NA ZAČÁTKU hovoru řekni, že jsi automatická AI asistentka (je to povinnost). "
        "TVŮJ ÚKOL: " + cil + " "
        "Drž se svého úkolu. Když si nejsi jistá, jde o něco mimo rozsah, nebo o citlivé či "
        "sporné rozhodnutí, slušně předej člověku — napiš na samostatný řádek [PREDANI] a "
        "stručný důvod. Nikdy si nevymýšlej data ani čísla; co nevíš, přiznej."
    )


def relace_start(tenant_id=None, kanal=None, protistrana=None, kontext=None, smer="prichozi"):
    from core.database import get_session
    if not tenant_id or not kanal:
        return {"ok": False, "error": "tenant_id a kanal (kod) jsou povinne"}
    sg = get_session()
    try:
        k = sg.execute(_t("SELECT id FROM hlas.kanal WHERE tenant_id=:t AND kod=:k"),
                       {"t": tenant_id, "k": kanal}).scalar()
        if not k:
            return {"ok": False, "error": "kanal '%s' neexistuje (tenant %s)" % (kanal, tenant_id)}
        rid = sg.execute(_t(
            "INSERT INTO hlas.relace (tenant_id, kanal_id, smer, protistrana, kontext) "
            "VALUES (:t,:k,:s,:p,CAST(:kx AS jsonb)) RETURNING id"),
            {"t": tenant_id, "k": k, "s": smer, "p": protistrana, "kx": _json.dumps(kontext or {})}).scalar()
        sg.commit()
        return {"ok": True, "columns": ["relace_id", "kanal_id"], "rows": [[rid, k]]}
    except Exception as e:
        try:
            sg.rollback()
        except Exception:
            pass
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:300])}
    finally:
        sg.close()


def relace_turn(relace_id=None, text=None, model=None):
    from core.database import get_session
    if not relace_id:
        return {"ok": False, "error": "relace_id je povinny"}
    sg = get_session()
    try:
        r = sg.execute(_t(
            "SELECT r.stav, k.nazev, k.config FROM hlas.relace r JOIN hlas.kanal k ON k.id=r.kanal_id "
            "WHERE r.id=:i"), {"i": relace_id}).first()
        if not r:
            return {"ok": False, "error": "relace %s neexistuje" % relace_id}
        stav0, nazev, cfg = r[0], r[1], r[2]
        hist = sg.execute(_t(
            "SELECT mluvci, text FROM hlas.relace_udalost WHERE relace_id=:i "
            "AND mluvci IN ('uzivatel','asistent') ORDER BY poradi"), {"i": relace_id}).fetchall()
        maxp = sg.execute(_t("SELECT COALESCE(MAX(poradi),0) FROM hlas.relace_udalost WHERE relace_id=:i"),
                          {"i": relace_id}).scalar()
        messages = [{"role": "user" if m == "uzivatel" else "assistant", "content": tx} for m, tx in hist]
        if text:
            messages.append({"role": "user", "content": text})
        if not messages:
            messages.append({"role": "user", "content": "(hovor začíná, pozdrav a představ se)"})
        system = _persona_system(nazev, cfg)
        model = model or _cfg_dict(cfg).get("model")
        reply, toks = _llm_reply(system, messages, model=model)
        reply_norm = _normtext(reply)
        novy_stav = stav0
        up = reply.upper()
        if "[PREDANI]" in up or "[PŘEDÁNÍ" in up:
            novy_stav = "predano_cloveku"
        p = maxp
        if text:
            p += 1
            sg.execute(_t("INSERT INTO hlas.relace_udalost (relace_id,poradi,mluvci,text) "
                          "VALUES (:i,:p,'uzivatel',:tx)"), {"i": relace_id, "p": p, "tx": text})
        p += 1
        sg.execute(_t("INSERT INTO hlas.relace_udalost (relace_id,poradi,mluvci,text,meta) "
                      "VALUES (:i,:p,'asistent',:tx,CAST(:m AS jsonb))"),
                   {"i": relace_id, "p": p, "tx": reply_norm,
                    "m": _json.dumps({"tokeny": toks, "surovy": reply})})
        if novy_stav != stav0:
            sg.execute(_t("UPDATE hlas.relace SET stav=:s WHERE id=:i"), {"s": novy_stav, "i": relace_id})
        sg.commit()
        return {"ok": True, "columns": ["role", "text", "stav"],
                "rows": [["Marti-AI", reply_norm, novy_stav]]}
    except Exception as e:
        try:
            sg.rollback()
        except Exception:
            pass
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:400])}
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
    if op == "relace_start":
        return relace_start(**args)
    if op == "relace_turn":
        return relace_turn(**args)
    if op == "voice_complete":
        from modules.erp.api.hlas_voice import build_reply as _br
        return {"ok": True, "columns": ["vystup"], "rows": [[_br(**args)]]}
    return {"ok": False, "error": "neznamy op '%s' (znam: kanal_upsert, normalizuj, vyslovnost_add, "
            "vyslovnost_seed_default, relace_start, relace_turn)" % op}
