# Most tise orezaval koncovy newline obsahovych zapisu - opraveno (newline-safe slepovani)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Symptom (nalez Jirka/C28 17.8.2026)
Zapis obsahu pres most (@@G2007SOUBOR) prisel o koncovy \n. U mobilnich dilku (typ='zdroj') se to projevilo az pri slepovani: kdyz posledni radek dilku byl // komentar bez koncove newline, po slepeni s dalsim dilkem zakomentoval jeho prvni radek -> appka spadla. Tise, nikde chyba.

## Root cause
`diag_sql` v router.py (radek ~39678): `sql = (str(body.get("sql") or "")).strip()` orezava trailing whitespace CELEHO SQL vc. koncove newline obsahu.

## Oprava (C24/Kristy 17.8.2026, commit d57d9ef9)
1. `@@G2007SESTAV` i `@@G2007PUBLISH` (skladany artefakt): slepuji fragmenty NEWLINE-SAFE (kazdy fragment zakoncen newline PRED slepenim). NENI to <script> separator (ten rozbil sdileny closure 1.8.), jen radkovy zlom.
2. `@@G2007SOUBOR`: uklada obsah VZDY s koncovou newline (idempotentne).
Overeno: unit test, py_compile, zivy @@G2007PUBLISH mobile.html se self-testem.

## Poucemi
Pro BYTOVE PRESNE kriticke zapisy pouzij base64 + md5 verifikaci (raw UPDATE convert_from(decode(...,'base64'),'UTF8')) - obchazi .strip() uplne. Bezna cesta @@G2007SOUBOR je uz proti newline-crashi bezpecna.

