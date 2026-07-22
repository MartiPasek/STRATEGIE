"""Hlas engine — app-level operace (zapis pres @@HLAS z mostu).
Integrita mekkych odkazu (entita_id/graf_id/domain_key) se hlida ZDE na app
vrstve — schema hlas nema cross-schema FK do g2007 (volba B, Marti 22.7.2026)."""
import json as _json
from sqlalchemy import text as _t


def _one(sg, sql, **p):
    return sg.execute(_t(sql), p).scalar()


def hlas_kanal_upsert(tenant_id=None, kod=None, nazev=None, typ="text", entita_id=None,
                      domain_key=None, graf_id=None, config=None, stav="navrh", poradi=0):
    """Zaloz/uprav kanal. Mekke odkazy se PRED zapisem overi na app vrstve."""
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
    """Genericky router pro @@HLAS. payload = dict s klicem 'op'."""
    if not isinstance(payload, dict):
        return {"ok": False, "error": "payload musi byt JSON objekt"}
    op = (payload.get("op") or "").strip()
    args = {k: v for k, v in payload.items() if k != "op"}
    if op == "kanal_upsert":
        return hlas_kanal_upsert(**args)
    return {"ok": False, "error": "neznamy op '%s' (znam: kanal_upsert)" % op}
