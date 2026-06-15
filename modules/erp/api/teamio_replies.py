# -*- coding: utf-8 -*-
"""Teamio — Candidate Applications Export (Replies Export API) — parser + klient.

Stav 15.6.2026: parser OVĚŘEN na vzorovém XML z dokumentace (jan.novak…).
Živé volání čeká na přístupy od LMC v env: TEAMIO_REPLIES_URL/USER/PASS
(zadá Marti do AppEnvironmentExtra, NE Claude). Bez nich je modul inertní.

Dokumentace:
  https://integrations.almacareer.com/teamio/replies-export-api/
  - request: GET <URL>?login=&password=&type=3 [&from&until&fromTime&untilTime]
    default = posledních 5 dní, max 200 odpovědí/volání, min 60 s mezi voláními
    (doporučeno á 30 min).
  - XML: candidateList → candidate (id) → parameterList / personalProfile /
    attachementList / GDPR. Namespace http://www.onrea.net/ei_std_cd/2010-02-16.

Typy příloh (description):
  CV:    208700001 (z profilu uchazeče) | 208700010 (přiložené ve formuláři)
  cover: 208700013 (motivační dopis, plain text)
  other: 208700002
  form:  208700004 (JOF) | 208700003 (Flexi dotazník)
"""
import base64
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

CV_DESC = {"208700001", "208700010"}
COVER_DESC = {"208700013"}
OTHER_DESC = {"208700002"}
FORM_DESC = {"208700004", "208700003"}


def _ln(tag):
    return tag.rsplit("}", 1)[-1]


def _find(el, name):
    for c in el.iter():
        if _ln(c.tag) == name:
            return c
    return None


def _findall(el, name):
    return [c for c in el.iter() if _ln(c.tag) == name]


def _txt(el):
    return (el.text or "").strip() if el is not None else None


def classify(desc):
    if desc in CV_DESC:
        return "cv"
    if desc in COVER_DESC:
        return "cover"
    if desc in FORM_DESC:
        return "form"
    return "other"


def parse_replies(xml_str):
    """XML (str) → list dictů kandidátů. Přílohy: name, desc, kind, content_type,
    data (bytes, dekódované z Base64)."""
    root = ET.fromstring(xml_str)
    out = []
    for c in [x for x in root.iter() if _ln(x.tag) == "candidate"]:
        rec = {"teamio_candidate_id": c.get("id"), "params": {}, "attachments": []}
        for p in _findall(c, "parameter"):
            rec["params"][p.get("name")] = (p.text or "").strip()
        cinfo = _find(c, "contactInformation")
        if cinfo is not None:
            nm = _find(cinfo, "name")
            fn = _txt(_find(nm, "firstName")) if nm is not None else None
            sn = _txt(_find(nm, "surname")) if nm is not None else None
            rec["first_name"], rec["surname"] = fn, sn
            rec["full_name"] = " ".join([x for x in (fn, sn) if x]) or None
            rec["email"] = _txt(_find(cinfo, "email"))
            rec["phone"] = _txt(_find(cinfo, "phone"))
        g = _find(c, "GDPR")
        if g is not None:
            rec["gdpr_valid_to"] = _txt(_find(g, "consentValidTo"))
            rec["gdpr_processed_outside_eu"] = g.get("processedOutsideEU")
        pr = rec["params"]
        rec["vacancy_id"] = pr.get("pdjdId")
        rec["vacancy_name"] = pr.get("pdjdextname") or pr.get("pdjdintname")
        rec["reaction_ts"] = pr.get("reactionTimestamp")
        rec["source"] = pr.get("sourceDetailText_0")
        rec["status_code"] = pr.get("candidateStatus")
        rec["recruiter_email"] = pr.get("recruiterEmail")
        for a in _findall(c, "attachement"):
            desc = _txt(_find(a, "description"))
            cont = _find(a, "content")
            b64 = (cont.text or "").strip() if cont is not None else ""
            try:
                data = base64.b64decode(b64) if b64 else b""
            except Exception:
                data = b""
            rec["attachments"].append({
                "name": _txt(_find(a, "name")),
                "desc": desc,
                "kind": classify(desc),
                "content_type": _txt(_find(a, "contentType")),
                "data": data,
            })
        out.append(rec)
    return out


def build_url(date_from=None, date_until=None, time_from=None, time_until=None):
    """Sestaví request URL z env (TEAMIO_REPLIES_URL/USER/PASS). None = není
    nastaveno (čeká na LMC). type=3 = Replies Export."""
    base = os.environ.get("TEAMIO_REPLIES_URL")
    login = os.environ.get("TEAMIO_REPLIES_USER")
    pw = os.environ.get("TEAMIO_REPLIES_PASS")
    if not (base and login and pw):
        return None
    q = {"login": login, "password": pw, "type": "3"}
    if date_from:
        q["from"] = date_from
    if date_until:
        q["until"] = date_until
    if time_from:
        q["fromTime"] = time_from
    if time_until:
        q["untilTime"] = time_until
    sep = "&" if "?" in base else "?"
    return base + sep + urllib.parse.urlencode(q)


def fetch_replies(date_from=None, date_until=None, timeout=60):
    """Stáhne XML z Teamia a vrátí parsnuté kandidáty. RuntimeError, pokud
    nejsou přístupy. (Pozor: limit 200/volání, min 60 s mezi voláními.)"""
    url = build_url(date_from, date_until)
    if not url:
        raise RuntimeError("Teamio Replies přístupy nejsou nastaveny "
                           "(TEAMIO_REPLIES_URL/USER/PASS v AppEnvironmentExtra).")
    with urllib.request.urlopen(url, timeout=timeout) as r:
        xml_str = r.read().decode("utf-8", "replace")
    return parse_replies(xml_str)
