# Nález se vrací, dokud příčina trvá — pokud ho nezavřel člověk (Peťa 3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Nález se vrací, dokud příčina trvá

> oblast: `dochazka` · zadala Peťa 3. 9. 2026, nasadil Claude-26

## Díra, kterou to zavírá
Nález na jeden záznam vznikal **jen jednou za život** — zápis má
`ON CONFLICT (tenant_id, rule, entry_id) DO NOTHING`. Jakmile ho někdo zavřel,
kontrola ho **už nikdy nezaložila znovu**, i když chyba v datech zůstala. Fronta
„K vyřešení" tak nebyla seznam „co je špatně", ale „co se jednou všimlo a ještě
to nikdo neodklikl".

Takhle přežily srpnové úseky bez zakázky u Honomichla a Paška: nález existoval,
20. 8. se zavřel, zakázka zůstala prázdná a nikdo se o nich už nedozvěděl. Peťa
je 3. 9. našla očima v přehledu, ne z kontroly.

Peťa 3. 9. 2026: *„nález posílat pořád, dokud není vyřešen, a nebo úmyslně potvrzen,
že je ok."*

## Co je nasazeno (`att_anomaly_scan` v25)
Za úklidové dotazy přibyly dva kroky, které nález **znovu otevřou**
(`resolved_at = NULL`) pro pravidla `chybi_zakazka` a `chybi_cinnost`, když příčina
pořád platí. **Záměrně bez okna 14 dnů** — okno omezuje zakládání nových nálezů,
tady nález už existuje a jen se vrací.

## ⚠️ Jak se pozná, že nález zavřel ČLOVĚK (dvě podmínky, ne jedna)
1. **`resolved_by` je vyplněné** — člověk tlačítkem.
2. **NEBO existuje `tenant.att_audit` se `action='resolve'` k témuž píchnutí.**

Druhá podmínka je nutná: **`att_fix_resolve` doplňuje `resolved_by` až od verze 2,
která je živá od 25. 8. 2026 12:30.** Všechno, co člověk odklikl PŘED tím datem, má
`resolved_by` prázdné a podle prvního testu by vypadalo jako práce automatu.

Zjištěno naostro 3. 9. 2026 večer: Claude nejdřív z prázdného `resolved_by` usoudil,
že čtyři srpnové nálezy zavřel automat, a postavil na tom celé pravidlo. Audit ale
ukázal, že je 20. 8. ve 14:44 odklikla **Peťa** tlačítkem „V pořádku — vyřídit"
(`att_audit` 1061–1063, důvod „rrr"/„rrrr", časy sedí na mikrosekundu). Bez druhé
podmínky by se lidem znovu otevíralo to, co vědomě odbavili.

**Pravidlo pro příště: prázdné `resolved_by` NEZNAMENÁ, že to udělal automat.**
U čehokoli před 25. 8. 2026 se musí sáhnout do `att_audit`.

## Kolik to hned vrátí
**Nula** — ověřeno dotazem před nasazením i po opravě. Všechny příčiny se týž den
srovnaly ručně.

## Na co si dát pozor
- Vrácený nález může být **starší než 60 dnů**. U `superseded` záznamu ho fronta
  stejně schová (má vlastní okno); u platného se ukáže bez ohledu na stáří. Záměr.
- Platí zatím **jen pro tato dvě pravidla** — u nich existuje přesná podmínka příčiny
  (převzatá z jejich úklidových dotazů). U ostatních by se musela dopsat.
- Párování na `att_audit` je přes `entry_id`, ne přes id nálezu — když má jedno
  píchnutí víc nálezů, chová se to konzervativně (spíš nevrátí). Je to schválně.

## Souvisí
[[doc-dochazka-prah-01h-u-chybi-zakazka-cinnost-zrusen]] ·
[[doc-dochazka-prekryv-casu-blokuje-zezelenani-a-odbaveni-z-fronty]]

