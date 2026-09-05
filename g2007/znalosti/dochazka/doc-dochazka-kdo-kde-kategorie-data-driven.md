# Kdo kde mobil - kategorie data-driven a osvc_absence pod Volno

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> **OPRAVA 5. 9. 2026 - sekce Deploy nize UZ NEPLATI.** Publikuje se pres `@@G2007PUBLISH`,
> ne pres `@@G2007SESTAV`. Sebe-test `@@G2007PUBLISH` je opraveny
> (`doc-system-g2007-g2007publish-selftest-event-loop-starvation`) a `@@G2007SESTAV` vydava
> i cizi nepublikovanou praci. Zavazny postup drzi
> `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje` a
> `doc-system-strategie-po-updatu-g2007-soubor-nutny-publish`.
> Vecny obsah o kategoriich "kdo kde" nize plati dal. Rozhodl Jirka Honomichl 5. 9. 2026.

## Problem (6.8.2026, C24/Kristy)
V mobilni appce "Kdo kde" nebyla videt volna zivnostniku (OSVC). Backend endpoint att_whereabouts (g2007.python, active) je OK - vraci u kazde osoby kind = presne code z ciselniku tenant.att_entry_type. Chyba byla ve frontendu - funkce kdekdo() ve fragmentu apps/api/static/mobile_parts/50_skupiny_vyroba.js mela pevny allowlist 8 kategorii (GRP = prace, homeoffice, vacation, sick, medical, family_care, unpaid, nic). Kody mimo nej frontend tise zahazoval (gMeta fallback na nic, smycky v render prochazely jen GRP). Nejvic u OSVC - jejich hlavni typ volna je osvc_absence (Nepritomnost OSVC), ktery v GRP nebyl. Stejna dira skryvala i sickday (i u HPP), maternity, ostatni_nahrada, plac_volno_70/80/90.

## Oprava
kdekdo() prepsan na data-driven. buckets() vezme zname kategorie (GRP kvuli ikonam/poradi) a prida kazdy neznamy kod z dat jako vlastni dlazdici - zadny budouci typ absence uz nepropadne. normKind() s ALIAS sklada osvc_absence pod Volno (unpaid, volba Kristy). gMeta i obe smycky v render jedou pres buckets() misto GRP. Nasledne (tez 6.8.) rail vzdy vykresli zname kategorie i s 0 (prazdna = tlumena seda), neznama jen kdyz jsou v datech.

## Pouceni
Frontend zobrazujici hodnoty z ciselniku nesmi drzet pevny allowlist, ktery neznama odfiltruje - odvozuj mnozinu z dat, jinak novy att_entry_type code tise zmizi z UI.

## Deploy
`@@G2007SOUBOR` (uprav dilek), pak **`@@G2007PUBLISH apps/api/static_db/mobile.html`**.
Pred publikaci zkontroluj, co jeste ceka nepublikovane - publikace vypusti i cizi rozdelanou praci.

Pozn. k orezu koncoveho newline z puvodniho zneni - u `@@G2007SOUBOR` nikdo nemeril, jestli plati dal
(u `@@G2007ADD` plati); viz `doc-system-strategie-most-orez-koncove-newline-oprava`
a `doc-system-g2007-editace-znalosti-pres-most-bez-poskozeni`.

NEPLATI (do 5. 9. 2026 tu stalo): "@@G2007SOUBOR (runner orizne trailing newline - doplnit chr(10)
v DB, overit md5), pak @@G2007SESTAV apps/api/static_db/mobile.html (PUBLISH rozbity - selftest
deadlock). Pred SESTAV zkontrolovat pending fragmenty."

