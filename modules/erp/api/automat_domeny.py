# -*- coding: utf-8 -*-
"""G2007 Automaty — domenove status buildery (Pilir B, C23, 2.8.2026).

Rozsiruje `automat.py`, ANIZ by sahalo na jeho jadro (stejny vzor jako
`automat_eskalace.py` pro Pilir C) — DOMAIN_CHECKS se registruji do
`automat.py`'s `_CHECKS` presne jako WATCHERS.

Kazda check funkce tady dela DVOJI PRACI (na rozdil od infra watcheru v
automat_eskalace.py):
  1) vraci (vysledek, zprava, rows, context) jako kazdy jiny automat —
     "vysledek" je tu skoro vzdy 'ok', protoze tohle NENI health-check,
     je to byznysovy prehled (neuspech = jen kdyz je DB nedostupna);
  2) ZAROVEN si rovnou zapise vyrenderovany text do g2007.automat.status_block
     (+ status_block_updated_at) pres stejnou `sg` session, kterou pak
     `_run_work()` v automat.py commitne spolecne s ostatnimi zapisy behu.
     Zadna nova infrastruktura navic - jen UPDATE do sloupcu pridanych
     2.8.2026 (ALTER TABLE g2007.automat ADD domain_kod/status_block/
     status_block_updated_at, dle g2007.znalost#280/#281).

Navazuje na g2007.znalost#280 (architektura), #281 (implementacni plan,
krok 4), #283 (poptavky/kalkulace/nabidky), #313/#314 (stav 2.8.2026).
"""
import logging

_log = logging.getLogger(__name__)


def _check_poptavky_status(sg):
    """Prvni domenovy automat (POC) - domena 'poptavky'. Cte tenant.vp_poptavka
    (AI triaz z Faze 3, viz g2007.znalost#313) a stavi status_block pro
    injekci do promptu Martinky v domene poptavky."""
    from sqlalchemy import text as T
    from datetime import datetime, timezone

    counts = sg.execute(T(
        "SELECT typ, count(*) AS n FROM tenant.vp_poptavka GROUP BY typ"
    )).mappings().all()
    total = sum(r["n"] for r in counts)
    n_real = next((r["n"] for r in counts if r["typ"] == "poptavka"), 0)
    n_other = total - n_real

    rows = sg.execute(T(
        "SELECT id, zakaznik, predmet, jistota, created_at FROM tenant.vp_poptavka "
        "WHERE typ='poptavka' ORDER BY created_at"
    )).mappings().all()

    lines = ["[STAV DOMÉNY: poptávky — čerstvý právě teď]",
             "Skutečné poptávky (AI klasifikace, Fáze 3): %d" % n_real,
             "Ostatní e-maily v mailboxu (provozní/ostatní, NE poptávky): %d" % n_other]
    now = datetime.now(timezone.utc)
    for r in rows:
        dny = None
        try:
            ca = r["created_at"]
            if ca is not None:
                dny = (now - ca).days
        except Exception:  # noqa: BLE001
            pass
        lines.append("  - %s (jistota %s%%%s): %s" % (
            r["zakaznik"] or "?", r["jistota"] if r["jistota"] is not None else "?",
            (", %d dní" % dny) if dny is not None else "", r["predmet"] or ""))
    lines.append("Čeká na kalkulaci/nabídku: sledování zatím nepostaveno (Fáze 4 pipeline"
                 " chybí — viz g2007.znalost#313).")
    status_block = "\n".join(lines)

    try:
        sg.execute(T(
            "UPDATE g2007.automat SET status_block=:sb, status_block_updated_at=now() "
            "WHERE kod='poptavky_status'"), {"sb": status_block})
    except Exception as e:  # noqa: BLE001 — status_block zapis nesmi shodit health-check
        _log.warning("_check_poptavky_status: zapis status_block selhal: %s", e)

    zprava = "%d skutečných poptávek, %d ostatních e-mailů (celkem %d)." % (n_real, n_other, total)
    return "ok", zprava, total, status_block


DOMAIN_CHECKS = {
    "poptavky_status": _check_poptavky_status,
}
