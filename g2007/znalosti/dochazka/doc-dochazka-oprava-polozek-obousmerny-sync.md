# Oprava/storno docházky na POLOŽKÁCH + obousměrný sync hlavičky

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> Rozšíření [[doc-dochazka-att-entry-vyroba-work-kaskada]]. Kristý 31.7.2026: editace/storno se u pracovních segmentů dělá na POLOŽKÁCH (vyroba_work), ne na hlavičce; hlavička (att_entry) se z položek DOPOČÍTÁ. Obousměrný sync VEDLE kanonické kaskády hlavička→položky (nerozbíjí ji).

## Proč
Opravy docházky ukazují u multi-zakázkových dnů rozpad po zakázkách (stejně jako Docházka new; jen navíc pauzy). Uživatel opravuje tam, kde je detail = na položce. Hlavička má zůstat konzistentní automaticky.

## Endpoint POST /app/attendance/fix/polozka (router.py)
Body `{id=vyroba_work.id, action='edit'|'void', od, konec, project_ref, cinnost_id, reason}`. Povinný důvod, audit (`polozka_fix`/`polozka_void`), notifikace dotčenému, `_att_automat_recalc_day`. Práva jako fix/entry (`_att_can_fix`, `_att_period_locked`, scope emps). Centrálské položky (`source_system='centrala1'`) = opravit jen v Centrále. edit: validace časů (od<konec, <20h), překryv s JINOU aktivní položkou dne (dvojí počítání), zakázka pichatelná (Rezie ok bez kontroly), činnost aktivní.

## Přepočet hlavičky: _att_recompute_header_from_items(s, att_id)
Směr POLOŽKY→HLAVIČKA. `started_at=MIN(od)`, `ended_at=MAX(konec)` aktivních zavřených položek úseku; **hodiny = (konec−začátek) − přestávka = PŘÍTOMNOST, NE součet položek**. Důvod: mzdy počítají přítomnost; storno VNITŘNÍ položky nesnižuje zaplacený den (jen KRAJNÍ položka mění obálku a tím hodiny). Ověřeno Bláha 476 23.7.: součet položek 8,00 h (překryv zaokrouhlením) vs obálka 7,98 h → obálka je správná pro mzdy. 0 aktivních položek → celý úsek zmizel → hlavička `superseded`+`local_lock`. Superseded/běžící (konec NULL) hlavičku nesahá. `local_lock=true` (zrcadlení ze staré Centrály ji neoživí).

## Nerozbití kaskády
Recompute NEVOLÁ kaskádu hlavička→položky (položky jsou po zásahu autoritativní). Kaskáda při příštím běhu jen potvrdí (obálka = min/max položek → idempotentní; fill-edges dorovnává krajní položky na začátek/konec úseku = už platí). Overlap-guard: po přepočtu obálka hlavičky nesmí kolidovat se sousedním att_entry (`_att_fix_overlap`) → jinak rollback celé operace.

## Frontend dochazka-opravy.html
Pod-řádky rozpadu dostaly akce ✏️/🗑 (canP = `editable` (source≠centrala1) & `!j.locked` & `pid`). Inline formulář reuse `mkZak`/`mkCin`/`reasonBox`/`confirmBox`/`api`. Hlavička dál edituje typ/absence/pauzy (fix/entry). Pauzy zůstávají viditelné jen v Opravách (JEDINÝ rozdíl proti Docházce new). `/fix/day` polozky nesou `pid`/`cin_id`/`editable`.

Souvisí [[doc-dochazka-att-entry-vyroba-work-kaskada]] [[doc-dochazka-model-tabulky-dochazky]] [[doc-dochazka-dochazka-new-skryva-dochazku]].

