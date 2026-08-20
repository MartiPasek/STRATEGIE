# Docházka: kaskáda att_entry↔vyroba_work — IMPLEMENTACE (30.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> Implementace modelu [[doc-dochazka-att-entry-vyroba-work-kaskada]]. Nasadil C24 (Kristý) 30.7.2026 večer. HOTOVO + backfill července ověřen.

## Kód
- Funkce `_att_sync_vyroba_work(s, employee_id, den, dry_run=False, create_missing=True)` v `modules/erp/api/router.py`. Vrací plán (deactivate/clip/dedup_off/create + segs/rows/settled). `dry_run=True` nic nezapíše.
- Volají ji: `att_fix_entry` (nahradila dřívější „krok-5" časové okno; propis zakázky/činnosti editora zůstává, cíleno `att_entry_id=nid` PO kaskádě), `att_fix_add` (po INSERTu položky), `att_fix_void` (sjednoceno: deaktivace vlastních položek přes att_entry_id + kaskáda), `att_fix_merge` (sešití; běžící sloučení chráněno).
- Backfill endpoint: `POST /api/v1/erp/app/attendance/fix/resync` (parent NEBO plný scope). Tělo `{from,to,uid?,dry_run=true,create=false}`. Vrací souhrn + ukazka + podezrele.

## Rozhodnutí (závazná)
1. VYPLŇ OKRAJE ÚSEKU (Kristý 30.7.): když oprava prodlouží konec/posune začátek úseku za krajní položku, první položka se dorovná k začátku úseku a poslední (dle max konec) k jeho konci → rozpad na zakázky SEDÍ s hlavičkou (Docházka new = Opravy), přidaný čas připadne na krajní zakázku. Vnitřní mezery mezi RŮZNÝMI činnostmi se NEvyplňují.
2. DEDUP jen SOUVISLÉ běhy stejné (zakázka, činnost) v úseku → span. Proložené činnosti A,B,A se NEslučují (span by přeskočil B → zdvojení hodin). Klíč = (zakázka, cinnost_id).
3. Guard SETTLED = běžící den (platný work/overhead/homeoffice úsek bez konce). Když je den živý → kaskáda NEdeaktivuje nekryté řádky a NEzakládá placeholdery (jinak by shodila zavřené položky živého dne). Ořez/dedup zavřených položek běží pořád. Běžící vyroba_work řádek (konec IS NULL) se vždy nechává žít.
4. Backfill default `create=false` — NEzakládat prázdné placeholdery lidem bez rozpadu na zakázky (kanceláře co nepíchají „Makám"). Interaktivní opravy (att_fix_*) placeholder zakládají (create_missing=True default).
5. Bere JEN naše nativní položky (`source_system<>'centrala1'` — EC agregát se nechává), jen `konec IS NOT NULL`. Absence do vyroba_work NEPATŘÍ (superseded/absence úsek není platný → jeho položky se deaktivují).

## GOTCHAS (drahé lekce)
- api_router má PREFIX `/api/v1/erp` → endpoint je na `/api/v1/erp/app/attendance/fix/resync` (ne `/app/...`). Volání bez prefixu = 404.
- Backfill CELÉHO měsíce v JEDNOM HTTP requestu (1171 dvojic) ZAHLTIL API → 502 gateway + 503 na ostatních endpointech. Fix: resync COMMITUJE PO DNI (resumovatelné, idempotentní, nedrží obří transakci) A pouštět po TÝDNECH (krátké requesty pod gateway timeout). Původní jedno-commit verze při pádu requestu NIC nezapsala (bezpečné, ale API spadlo).
- Práva: parent (is_marti_parent) NEMÁ automaticky `att_fix_scope.fix_all` → resync explicitně povolen pro plný scope NEBO rodiče.

## Backfill VII 2026 (ověřeno)
Po týdnech: clip 1234, dedup 24, deactivate 12 (všech 12 osiřelých, 0 zbylo), create 0. Suma vyroba_work VII = 4319,8 h (žádné ztráty). Petra cz1 9.7.: HO 08:19-15:59 (dotaženo k hlavičce) + work 21:01-23:59. Živý test opravou prošel. test_kaskada.py 9/9 PASS.

## Commity
5d3c9793 (vyplň okraje), 47d8f725 (resync i rodičům), 5ce6fd2c (přepínač create), 6a7738d2 (commit po dni). Kaskáda+napojení: 38859537.

