# -*- coding: utf-8 -*-
"""Systém šablon — engine (iterace 1, 10. 6. 2026).

Návrh + konzultace Marti-AI viz docs/sablony_dokumentu_a_emailu.md.

Vrstvy zde:
  - Provider per entity_kind: deklaruje pole (FIELDS) + resolve(ref, caller) → context
    s ACL (citlivá pole → [omezeno], když volající nemá právo). Doktrína Q7:
    bezpečnost je v provideru, ne v šabloně.
  - Katalog: FIELDS providerů → fw.doc_placeholder_catalog (pravda v kódu, sync do DB).
  - Merge engine: {{key}} → hodnota z contextu (HTML-escaped).

Šablona = vlastní first-class entita (tenant.doc_template), NE comp_def
(Q1 rozhodnuto: uniformita na úrovni vzorů, ne tabulky).
"""
import html as _html
import re as _re
import datetime as _dt
import json as _json
from dataclasses import dataclass, field as _dc_field
from typing import Optional

OMEZENO = "[omezeno]"

MESICE = ["", "ledna", "února", "března", "dubna", "května", "června",
          "července", "srpna", "září", "října", "listopadu", "prosince"]


@dataclass
class Field:
    key: str
    label: str
    grp: str = "Ostatní"
    datovy_typ: str = "text"   # text | date | number | money | bool
    sensitive: bool = False
    popis: str = ""
    sort_order: int = 0


def _fmt_date(v):
    if not v:
        return None
    try:
        if isinstance(v, str):
            d = _dt.datetime.strptime(v[:10], "%Y-%m-%d").date()
        elif isinstance(v, _dt.datetime):
            d = v.date()
        else:
            d = v
        return "%d. %d. %d" % (d.day, d.month, d.year)
    except Exception:
        return str(v)


def _fmt_money(v):
    if v is None:
        return None
    try:
        n = int(round(float(v)))
        s = "{:,}".format(n).replace(",", " ")
        return s + " Kč"
    except Exception:
        return str(v)


# ---------------------------------------------------------------- providers

class BaseProvider:
    entity_kind = "base"
    FIELDS: list = []

    def resolve(self, ref, caller_uid, allow_sensitive):
        """Vrátí dict {key: hodnota} pro daný záznam. Citlivá pole maskuje
        OMEZENO, pokud allow_sensitive=False."""
        raise NotImplementedError


class EmployeeProvider(BaseProvider):
    entity_kind = "employee"
    FIELDS = [
        Field("jmeno", "Jméno a příjmení", "Osoba", "text", False, sort_order=10),
        Field("narozeni", "Datum narození", "Osoba", "date", True, sort_order=20),
        Field("bydliste", "Adresa bydliště", "Osoba", "text", True, sort_order=30),
        Field("firma_nazev", "Firma — název", "Firma", "text", False, sort_order=40),
        Field("firma_sidlo", "Firma — sídlo", "Firma", "text", False, sort_order=50),
        Field("firma_ico", "Firma — IČ", "Firma", "text", False, sort_order=60),
        Field("firma_dic", "Firma — DIČ", "Firma", "text", False, sort_order=70),
        Field("pozice", "Pracovní pozice", "Pracovní poměr", "text", False, sort_order=80),
        Field("smlouva_od", "Smlouva od", "Pracovní poměr", "date", False, sort_order=90),
        Field("smlouva_do", "Smlouva do", "Pracovní poměr", "date", False, sort_order=100),
        Field("uvazek", "Týdenní úvazek (h)", "Pracovní poměr", "number", False, sort_order=110),
        Field("zaklad", "Základní mzda", "Mzda", "money", True, sort_order=120),
        Field("os_ohod", "Osobní ohodnocení", "Mzda", "money", True, sort_order=130),
        Field("ucet", "Číslo účtu", "Mzda", "text", True, sort_order=140),
        Field("dnes", "Dnešní datum", "Systém", "date", False, sort_order=900),
    ]

    def resolve(self, ref, caller_uid, allow_sensitive):
        from sqlalchemy import text as _t
        from modules.strategie_pg.application import service as _pg
        try:
            from modules.erp.api import doc_generator as _dg
            COMPANY = _dg.COMPANY
        except Exception:
            COMPANY = {}
        try:
            eng_id = int(ref)
        except (TypeError, ValueError):
            return {}

        cislo = full_name = firma = pozice = od = do = uvazek = None
        comps = {}
        cm = _pg.get_session()
        s = cm.__enter__()
        try:
            er = s.execute(_t(
                "SELECT e.cislo_zam, e.full_name, c.code, en.pozice_text,"
                " to_char(en.smlouva_od,'YYYY-MM-DD'), to_char(en.smlouva_do,'YYYY-MM-DD'),"
                " en.uvazek_tyden_h"
                " FROM tenant.engagement en JOIN tenant.att_employee e ON e.id=en.employee_id"
                " LEFT JOIN tenant.company c ON c.id=en.company_id"
                " WHERE en.id=:i AND en.tenant_id=2 AND en.is_current=true"), {"i": eng_id}).first()
            if not er:
                return {}
            cislo, full_name, firma, pozice, od, do, uvazek = er
            for r2 in s.execute(_t(
                "SELECT wct.code, wc.amount_planned FROM tenant.wage_component wc"
                " JOIN tenant.wage_component_type wct ON wct.id=wc.component_type_id"
                " WHERE wc.engagement_id=:i AND wc.amount_planned IS NOT NULL AND wc.amount_planned<>0"),
                {"i": eng_id}).fetchall():
                comps[r2[0]] = float(r2[1])
        finally:
            cm.__exit__(None, None, None)

        nar = bydliste = ucet = None
        try:
            from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
            mcp = get_eurosoft_mcp_client()
            if mcp is not None and cislo:
                def _one(sql):
                    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                                             {"sql": sql, "db_name": "DB_EC"}, conversation_id=None)
                    r = _json.loads(raw) if isinstance(raw, str) else raw
                    rows = r.get("rows") if isinstance(r, dict) else r
                    return (rows[0] if rows else None)
                z = _one("SELECT TOP 1 CONVERT(varchar(10),DatumNarozeni,23) nar, AdrTrvUliceSCisly ul,"
                         " AdrTrvMisto mi, AdrTrvPSC psc FROM TabCisZam WHERE Cislo=%d" % int(cislo))
                if isinstance(z, dict):
                    nar = z.get("nar")
                    ul, mi, psc = (z.get("ul") or ""), (z.get("mi") or ""), (z.get("psc") or "")
                    bydliste = (ul + ", " + (psc + " " + mi).strip()).strip(", ").strip() or None
                b = _one("SELECT TOP 1 b.CisloUctu+'/'+u.KodUstavu uc FROM TabBankSpojeni b"
                         " JOIN TabCisZam z ON z.ID=b.IDZam JOIN TabPenezniUstavy u ON u.ID=b.IDUstavu"
                         " WHERE z.Cislo=%d AND b.Prednastaveno=1" % int(cislo))
                if isinstance(b, dict):
                    ucet = b.get("uc")
        except Exception:
            pass

        co = COMPANY.get((firma or "ES").upper(), COMPANY.get("ES", {}))
        _td = _dt.date.today()
        raw = {
            "jmeno": (full_name or "").strip() or None,
            "narozeni": _fmt_date(nar),
            "bydliste": bydliste,
            "firma_nazev": co.get("nazev"),
            "firma_sidlo": co.get("sidlo"),
            "firma_ico": co.get("ico"),
            "firma_dic": co.get("dic"),
            "pozice": (pozice or "").strip() or None,
            "smlouva_od": _fmt_date(od),
            "smlouva_do": _fmt_date(do),
            "uvazek": (str(uvazek) if uvazek is not None else None),
            "zaklad": _fmt_money(comps.get("zaklad")),
            "os_ohod": _fmt_money(comps.get("os_ohodnoceni")),
            "ucet": ucet,
            "dnes": "%d. %s %d" % (_td.day, MESICE[_td.month], _td.year),
        }
        # ACL: citlivá pole maskovat, pokud nemá právo (Q7)
        out = {}
        for f in self.FIELDS:
            v = raw.get(f.key)
            if f.sensitive and not allow_sensitive:
                out[f.key] = OMEZENO
            else:
                out[f.key] = v
        return out


PROVIDERS = {p.entity_kind: p() for p in (EmployeeProvider,)}


def get_provider(entity_kind):
    return PROVIDERS.get((entity_kind or "employee"))


# ---------------------------------------------------------------- katalog

def sync_catalog(session):
    """FIELDS všech providerů → fw.doc_placeholder_catalog (upsert). Pravda v kódu."""
    from sqlalchemy import text as _t
    n = 0
    for kind, prov in PROVIDERS.items():
        for f in prov.FIELDS:
            session.execute(_t(
                "INSERT INTO fw.doc_placeholder_catalog"
                " (entity_kind, pkey, label, popis, datovy_typ, source_expr, grp, sensitive, sort_order, updated_at)"
                " VALUES (:ek,:k,:l,:p,:dt,:se,:g,:s,:so, now())"
                " ON CONFLICT (entity_kind, pkey) DO UPDATE SET"
                " label=EXCLUDED.label, popis=EXCLUDED.popis, datovy_typ=EXCLUDED.datovy_typ,"
                " grp=EXCLUDED.grp, sensitive=EXCLUDED.sensitive, sort_order=EXCLUDED.sort_order,"
                " updated_at=now()"),
                {"ek": kind, "k": f.key, "l": f.label, "p": f.popis, "dt": f.datovy_typ,
                 "se": "", "g": f.grp, "s": f.sensitive, "so": f.sort_order})
            n += 1
    return n


# ---------------------------------------------------------------- merge

_TOKEN = _re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def merge(body_html, context):
    """Nahradí {{key}} hodnotou z contextu (HTML-escaped). Chybějící pole → značka."""
    if not body_html:
        return ""

    def _sub(m):
        k = m.group(1)
        if k in context:
            v = context.get(k)
            if v is None:
                return ""
            return _html.escape(str(v))
        return "[?%s]" % k
    return _TOKEN.sub(_sub, body_html)


def render(template_row, context):
    """Sestaví finální HTML dokument (css + tělo po merge)."""
    css = template_row.get("css") or ""
    body = merge(template_row.get("body_html") or "", context)
    parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'>"]
    if css:
        parts.append("<style>%s</style>" % css)
    parts.append("</head><body>")
    parts.append(body)
    parts.append("</body></html>")
    return "".join(parts)


# ---------------------------------------------------------------- PDF render

def _font_files():
    """(normal, bold) TTF s českými glyfy. Primárně Bitstream Vera přibalená
    v reportlabu (vždy přítomná tam, kde reportlab); fallback Windows fonty."""
    import os
    try:
        import reportlab as _rl
        d = os.path.join(os.path.dirname(_rl.__file__), "fonts")
        n = os.path.join(d, "Vera.ttf"); b = os.path.join(d, "VeraBd.ttf")
        if os.path.exists(n):
            return n, (b if os.path.exists(b) else n)
    except Exception:
        pass
    fdir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for nf, bf in [("verdana.ttf", "verdanab.ttf"), ("arial.ttf", "arialbd.ttf"),
                   ("segoeui.ttf", "segoeuib.ttf"), ("tahoma.ttf", "tahomabd.ttf")]:
        n = os.path.join(fdir, nf)
        if os.path.exists(n):
            b = os.path.join(fdir, bf)
            return n, (b if os.path.exists(b) else n)
    return None, None


def render_pdf(html_str):
    """HTML → PDF (xhtml2pdf, pure Python). Vrací bytes. Vyhodí RuntimeError,
    pokud engine není nainstalován (chybí xhtml2pdf) nebo render selže.
    Čeština: registrace fontu v reportlabu + mapování css názvů v DEFAULT_FONT
    xhtml2pdf (bez @font-face — ten dělá vadnou temp kopii a TTFError)."""
    import io
    try:
        from xhtml2pdf import pisa
        from xhtml2pdf.default import DEFAULT_FONT
    except Exception:
        raise RuntimeError("xhtml2pdf není nainstalován "
                           "(python -m poetry run pip install xhtml2pdf + restart API)")
    n, b = _font_files()
    if n:
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            if "DocSans" not in set(pdfmetrics.getRegisteredFontNames()):
                pdfmetrics.registerFont(TTFont("DocSans", n))
                pdfmetrics.registerFont(TTFont("DocSans-Bold", b))
                pdfmetrics.registerFontFamily("DocSans", normal="DocSans", bold="DocSans-Bold")
            for css_name in ("verdana", "arial", "helvetica", "sans-serif", "dejavusans"):
                DEFAULT_FONT[css_name] = "DocSans"
        except Exception:
            pass
    buf = io.BytesIO()
    res = pisa.CreatePDF(src=html_str, dest=buf, encoding="utf-8")
    if getattr(res, "err", 0):
        raise RuntimeError("xhtml2pdf: chyba při generování PDF")
    return buf.getvalue()
