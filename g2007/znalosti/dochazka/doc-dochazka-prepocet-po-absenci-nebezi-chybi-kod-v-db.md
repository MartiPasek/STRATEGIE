# Přepočet „doplnění do fondu" po zadání absence NEBĚŽÍ — volaný kód v g2007.python neexistuje (25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Přepočet po zadání absence se nespouští (25. 8. 2026)

Zjistil Claude-28 při ověřování sick day na budoucí den, na zadání **Jirky Honomichla**.
Schválila **Marti-AI** (msg 13691) předání Peťě Šafránkové; e-mail jí odešel 25. 8. v 10:36.

## Co je špatně

`att_absence` (g2007.python, v16) má po zápisu absence přepočítat **doplnění do fondu**
a **nenárokovou práci** pro všechny dotčené dny. Peťa to tam přidala 4. 8. 2026 s odůvodněním
*„jinak zůstanou staré hodnoty"*.

Volá se takto:

```python
try:
    _dd = d0
    while _dd <= d1:
        _att_automat_recalc_day(emp, _dd)   # -> _ereg.call("att_automat_recalc_day", ...)
        _dd = _dd + _td(days=1)
except Exception:
    pass
```

**Jenže `att_automat_recalc_day` v `g2007.python` NEEXISTUJE** — ověřeno 25. 8. 2026 dotazem
bez filtru na `stav_zivota`: v tabulce není ani jako `navrzeno`/`inactive`. Existuje jen
`att_automat_level_day` (v8).

## Proč to nespadne a nikdo se to nedozví

`erp_registry.call()` **do jádra nesahá** (`modules/erp/api/erp_registry.py:36–42`):

```python
row = _load_active(kod)
if not row:
    raise RuntimeError("g2007.python: kod '%s' nema aktivni implementaci ..." % kod)
```

Žádný fallback na `router.py`. Přitom **v jádru ta funkce žije** a má plné tělo
(`router.py:28581`, Peťa 20. 7. 2026, s poznámkou *„NIKDY nevyhodí výjimku"*) — volají ji
odtud `dochazka_absence_sprava.py` i `dochazka_zak_tab.py`. Ale cesta z `att_absence`
jde přes DB, a tam kód chybí.

Výsledek: `RuntimeError` → spolkne ho `except Exception: pass` → **navenek se nic neděje**.

## Dopad

**Nezměřeno.** Ověřená je jen ta ingredience — že se volání nikdy nepovede. Kolika dnů
a kterých lidí se dotklo, že jim zůstalo staré „doplnění do fondu", **nikdo nespočítal**;
netvrdit dopad, dokud se to nezměří.

## Co s tím

Předáno **Peťě Šafránkové** (e-mail 25. 8. 2026 10:36, `public.email_outbox` id 660) —
je to její kód a její odůvodnění, takže rozhoduje ona, jestli chybějící kód domigrovat,
nebo volání přesměrovat do jádra.

⚠️ **Poučení nad rámec tohohle případu:** `try/except Exception: pass` kolem
`erp_registry.call()` **umlčí i to, že volaný kód v DB vůbec není**. Kdekoli se migrovaný
kód volá takhle, stojí za to ověřit, že cíl v `g2007.python` **existuje jako `active`** —
jinak funkce tiše nedělá nic.

Souvisí: [[doc-dochazka-sickday-budouci-den-se-tise-ztrati]] ·
[[doc-system-g2007-smer-zdroj-pravdy-python-soubor-2026-08-01]]

