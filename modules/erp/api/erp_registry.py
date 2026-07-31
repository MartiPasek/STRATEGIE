# -*- coding: utf-8 -*-
"""erp_registry — dynamicke nacteni a spusteni ERP funkci z g2007.python bez restartu API.
Vzor 1:1 s tool_registry/runtime.py (Tool Factory, 22.7.2026). Zdroj pravdy = radek v
g2007.python, NE soubor na disku. C23, 31.7.2026, Marti OK (viz G2007
doc-system-strategie-vize-kod-jako-data-bez-restartu + doc-system-g2007-expected-version-implementace-pripraveno).

STAV: PRIPRAVENO, NEPOUZIVANO ZADNOU ZIVOU CESTOU. Bezpecne k importu (nic samo nespusti).
Aktivace = az kdyz konkretni volajici (napr. _mzdy_absence_rows v router.py) zacne volat
erp_registry.call(...) misto vlastniho tela — to je samostatny, explicitni krok s deployem.

Kontrakt: kazdy radek v g2007.python ma sloupec `zdroj` = python text obsahujici funkci
`run(*args, **kwargs)`. Nacte se pres compile()+exec() do izolovaneho namespace, jednou per
verze (in-memory cache podle (kod, verze)), pak se `run` zavola s predanymi argumenty. Zadny
restart procesu, zadny soubor na disku. Zmena verze v DB (trigger g2007.fn_python_archiv_pred_update
inkrementuje verze pri kazde zmene zdroje) = priste volani si samo natahne novou verzi.
"""
import threading

_cache_lock = threading.Lock()
_cache = {}  # kod -> (verze, callable)


def _load_active(kod):
    from sqlalchemy import text as _t
    from core.database import get_session as _gg
    sg = _gg()
    try:
        row = sg.execute(_t(
            "SELECT zdroj, verze FROM g2007.python WHERE kod=:k AND stav_zivota='active'"),
            {"k": kod}).fetchone()
        return row
    finally:
        sg.close()


def call(kod, *args, **kwargs):
    """Zavolej aktivni implementaci `kod` z g2007.python. Cachuje zkompilovany kod podle verze."""
    with _cache_lock:
        cached = _cache.get(kod)
    row = _load_active(kod)
    if not row:
        raise RuntimeError("g2007.python: kod '%s' nema aktivni implementaci (stav_zivota='active')" % kod)
    zdroj, verze = row[0], row[1]
    if cached and cached[0] == verze:
        fn = cached[1]
    else:
        ns = {}
        exec(compile(zdroj, "<g2007.python:%s:v%s>" % (kod, verze), "exec"), ns)
        fn = ns.get("run")
        if not callable(fn):
            raise RuntimeError("g2007.python: kod '%s' verze %s nema funkci run()" % (kod, verze))
        with _cache_lock:
            _cache[kod] = (verze, fn)
    return fn(*args, **kwargs)


def selftest_compare(kod, legacy_fn, args, kwargs=None):
    """Porovna vystup aktivni/navrzene DB-implementace s puvodni (legacy_fn) na stejnych
    vstupech. POUZE PRO SEBETEST pred aktivaci — nevola se z produkcni cesty.
    Pozor: call() cte jen stav_zivota='active' — pro test funkce jeste ve stavu 'navrzeno'/
    'v_sandboxu' pouzij _load_by_kod_any_stav (nize) misto call()."""
    kwargs = kwargs or {}
    db_out = call(kod, *args, **kwargs)
    legacy_out = legacy_fn(*args, **kwargs)
    ok = (db_out == legacy_out)
    return {"ok": ok, "shoda": ok,
            "db_out_preview": repr(db_out)[:300], "legacy_out_preview": repr(legacy_out)[:300]}


def selftest_compare_any_stav(kod, legacy_fn, args, kwargs=None):
    """Jako selftest_compare, ale nacte NEJNOVEJSI radek pro `kod` bez ohledu na stav_zivota
    (pouziva se PRED aktivaci, kdy je radek jeste 'navrzeno'/'v_sandboxu')."""
    from sqlalchemy import text as _t
    from core.database import get_session as _gg
    kwargs = kwargs or {}
    sg = _gg()
    try:
        row = sg.execute(_t(
            "SELECT zdroj, verze FROM g2007.python WHERE kod=:k ORDER BY updated_at DESC LIMIT 1"),
            {"k": kod}).fetchone()
    finally:
        sg.close()
    if not row:
        return {"ok": False, "error": "kod '%s' v g2007.python neexistuje" % kod}
    zdroj, verze = row[0], row[1]
    ns = {}
    exec(compile(zdroj, "<g2007.python:%s:v%s:pretest>" % (kod, verze), "exec"), ns)
    fn = ns.get("run")
    if not callable(fn):
        return {"ok": False, "error": "kod '%s' verze %s nema funkci run()" % (kod, verze)}
    db_out = fn(*args, **kwargs)
    legacy_out = legacy_fn(*args, **kwargs)
    ok = (db_out == legacy_out)
    return {"ok": ok, "shoda": ok, "verze": verze,
            "db_out_preview": repr(db_out)[:300], "legacy_out_preview": repr(legacy_out)[:300]}
