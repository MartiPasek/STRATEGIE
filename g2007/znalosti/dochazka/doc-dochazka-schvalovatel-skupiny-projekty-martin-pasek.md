# Skupina „projekty" — schvalovatel volna přešel z Veverky na Martina Paška (31.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Skupina „projekty" — schvalovatel volna je Martin Pašek (od 31. 8. 2026)

**Zadala** Péťa Šafránková · **potvrdila** Kristý · **provedl** Claude-24, write #2647 · **ověřeno čtením i resolverem.**

## Co se změnilo

`tenant.att_approver_group` id 4 („projekty", member = post 53 VEDOUCÍ PROJEKTŮ (OBCHODNÍ ZÁSTUPCE), bez subtree)

- `att_approver` id 5 — Jiří Veverka (emp 3 / uid 106) → `aktivni=false`
- `att_approver` id 8 — **Martin Pašek (os. č. 29, emp 5 / uid 35)** → `aktivni=true`, bez zástupu

Tím je **§6.2 znalosti [[doc-dochazka-schvalovani-dovolene]] u řádku „projekty" zastaralá** (uvádí Veverku). Ostatní tři skupiny (výroba → Havlát/Honal, nákupčí → Petra Šafránková, fallback → Šárka Novotná) beze změny.

## Koho se to týká

Na postu 53 je 13 aktivních lidí. Přes skupinu jde **8 z nich** (ti, kdo nemají osobní výjimku v `att_odpovednost`) — ověřeno voláním `tenant.resolve_approvers(2, emp, CURRENT_DATE)`, všech 8 vrací Martina Paška

Kolářová (35), J. Svoboda (79), Horký (38), Dvořáková (24), Hellmayer (22), Jarrar (6), T. Veverková (4) a **Martin Pašek sám (5)**.

Zbylých 5 (Veverka, Zeman, Beneš, V. Mareš, Čepický) má osobní výjimku v `att_odpovednost`, ta má v `_abs_resolve` přednost — u nich změna nic nedělá. Veverka měl už od 6. 8. výjimku na Martina Paška, takže jemu vychází totéž oběma cestami.

## ⚠️ Vědomý důsledek — vlastní volno Martina Paška

Martin Pašek je sám na postu 53 a resolver žadatele vylučuje (`a.employee_id <> p_emp`), takže pro `emp 5` vrací **prázdno** (ověřeno). `_abs_resolve` pak spadne na fallback → **Šárka Novotná (13)**.

**Kristý 31. 8. rozhodla to tak nechat** (žádnou osobní výjimku mu nezakládat). Kdyby to mělo jít jinam, stačí řádek do `tenant.att_odpovednost` (agenda `volno`, user 35), kód se nemění. Do 31. 8. si Veverka a Martin Pašek schvalovali navzájem (žádosti 135/136/137).

## Podnět — co se ve skutečnosti stalo

Péťa hlásila, že jí přišla Veverkova dovolená. **Systém ji tak nesměroval** — žádosti #136 (28. 8.) a #137 (31. 8.) šly korektně na Martina Paška přes osobní výjimku. Péťě přišla **ruční zpráva v chatu** (`fw.mobile_command` 21733, 25. 8. 22.47, „🙋 Dotaz od Jiří Veverka — chtěl bych Tě požádat o schválení dovolené"). Vlastní volno Péti chodí podle `att_odpovednost` na Michelle Šafránkovou (17).

**Poučení** — než se přesměruje schvalovatel kvůli tomu, že „přišlo to špatnému člověku", ověř v `att_absence_request.manager_user_id`, kudy žádost skutečně šla. Ruční dotaz v chatu vypadá na mobilu skoro stejně jako routovaná žádost, ale se schvalovacím procesem nemá nic společného.

## Otevřené

Požadavek „vedoucí pracovníci nemusí chodit nikomu" (Péťa, povolil Marti) **dnes nejde nastavit daty** — `_abs_resolve` má tvrdý fallback a nikdy nevrátí prázdný seznam. Je to tentýž mechanismus, který chybí PLC OSVČ od 6. 8. Návrh (příznak v Podmínkách a bonusech, obdoba `pod_bez_dochazky`) leží v `docs/dochazka_bez_schvalovatele_navrh.md` — **neaktivováno, čeká na review s Martim.**

**Souvisí** [[doc-dochazka-schvalovani-dovolene]] · [[doc-dochazka-odpovednost-schvalovani-volna]] · [[doc-dochazka-schvalovani-absenci-kde-a-jak]]

