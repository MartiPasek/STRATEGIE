# Kdo kde mobil - kategorie data-driven a osvc_absence pod Volno

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Problem (6.8.2026, C24/Kristy)
V mobilni appce "Kdo kde" nebyla videt volna zivnostniku (OSVC). Backend endpoint att_whereabouts (g2007.python, active) je OK - vraci u kazde osoby kind = presne code z ciselniku tenant.att_entry_type. Chyba byla ve frontendu - funkce kdekdo() ve fragmentu apps/api/static/mobile_parts/50_skupiny_vyroba.js mela pevny allowlist 8 kategorii (GRP = prace, homeoffice, vacation, sick, medical, family_care, unpaid, nic). Kody mimo nej frontend tise zahazoval (gMeta fallback na nic, smycky v render prochazely jen GRP). Nejvic u OSVC - jejich hlavni typ volna je osvc_absence (Nepritomnost OSVC), ktery v GRP nebyl. Stejna dira skryvala i sickday (i u HPP), maternity, ostatni_nahrada, plac_volno_70/80/90.

## Oprava
kdekdo() prepsan na data-driven. buckets() vezme zname kategorie (GRP kvuli ikonam/poradi) a prida kazdy neznamy kod z dat jako vlastni dlazdici - zadny budouci typ absence uz nepropadne. normKind() s ALIAS sklada osvc_absence pod Volno (unpaid, volba Kristy). gMeta i obe smycky v render jedou pres buckets() misto GRP. Nasledne (tez 6.8.) rail vzdy vykresli zname kategorie i s 0 (prazdna = tlumena seda), neznama jen kdyz jsou v datech.

## Pouceni
Frontend zobrazujici hodnoty z ciselniku nesmi drzet pevny allowlist, ktery neznama odfiltruje - odvozuj mnozinu z dat, jinak novy att_entry_type code tise zmizi z UI.

## Deploy
@@G2007SOUBOR (runner orizne trailing newline - doplnit chr(10) v DB, overit md5), pak @@G2007SESTAV apps/api/static_db/mobile.html (PUBLISH rozbity - selftest deadlock). Pred SESTAV zkontrolovat pending fragmenty.

