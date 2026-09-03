# Podklad OSVČ: kontrola fakturace + oprava App hodin na uzavřených zakázkách

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Kontext
Rozklíčování podkladu fakturace OSVČ (3.9.2026, C24/Kristý + Dušan). Podklad = `g2007.python` `podklad_vyplaceni_pdf`. Vzniklo z něj: (a) oprava, (b) opakovatelná kontrola (skill `kontrola-podkladu-osvc`).

## NÁLEZ — App hodiny na uzavřených zakázkách propadaly
Podklad počítá po zakázkách ve 4 větvích: otevřená bez financí → STRATEGIE hodiny × sazba − už objednáno; **otevřená ve finančním plánu Centrály (`fin_map`, zbývá>1) → brala hodiny i částku z Centrály (`ec.zakazky_finance_zam`) a STRATEGIE hodiny zahodila**; vypořádaná (`ma_fin`, zbývá≤1) → přeskočena; uzavřená bez financí (`oz_zakazky._Uzavreno`) → přeskočena. Důsledek: když Centrála zakázku uzavře a ve STRATEGII na ní PŘIBYDOU hodiny (které se do Centrály nedostaly, protože app docházka nejde do `EC_Dochazka`), tyto hodiny se neproplatí. Konkrétně Voříšek (327) VR10654: STRATEGIE 41,78 h vs Centrála 32,55 h → chybělo 9,23 h ≈ 3 230 Kč. Zakázka uzavřena 10.7. (`_DatumVyhodnoceni`), jeho App píchání 15.6.+2.7. bylo PŘED uzávěrkou (nepíchal na zavřenou zakázku — jen se to nesynchronizovalo do Centrály včas).

## OPRAVA (nasazeno, verze 12)
Ve větvi `fin_map` se dopočítají STRATEGIE hodiny navíc proti Centrále:
```
_extra_h = (hod - fin_hodin) if hod > fin_hodin else Decimal(0)
zaklad = fin_vyplatit + _extra_h * sazba
hod_tisk = hod if hod > fin_hodin else (fin_hodin if fin_hodin > 0 else hod)
```
U zakázek, kde STRATEGIE ≤ Centrála (`_extra_h=0`), se nic nemění. Regrese: z 2795 uzavřených zakázek (170 s hodinami) se změnila JEN VR10654. **Zbývá dořešit** stejným principem větve `ma_fin` a „uzavřená bez financí" (dnes tam žádný OSVČ nespadá; při přechodu od Centrály můžou) + dedup pravidlo app/centrála. To je směr F1/F2 = STRATEGIE jako výhradní zdroj hodin, Centrála jen „už zaplaceno" + prémie/srážky.

## KONTROLA (skill `kontrola-podkladu-osvc`) — 4 kroky
1. **Hodiny**: odpracováno (`vyroba_work`, filtry `is_active`+`konec IS NOT NULL`+docházka ne `superseded`+`fakturace_obj_id IS NULL`) == co vstupuje do fakturace? Sken chybějících = zakázky kde STRATEGIE hodiny > Centrála (`fin_map`/`ma_fin`/uzavřená). Dedup app vs centrala1 přes sdílené `att_entry_id` (viselý odkaz sdílení nedokazuje).
2. **Sazba**: `vyplatit = hodiny × sazba − už objednáno`.
3. **Razítkování**: režie/dovolená se razítkují (`fakturace_obj_id`), cutoff = 1. den měsíce poslední režijní objednávky; před ním oražené, aktuální ne. Zakázky se nerazítkují.
4. **Objednávky**: „už objednáno" ≤ práce k **datu položky** (`TabPohybyZbozi.DatPorizeni`, NE hlavička — generuje se dopředu). Objednávka = měsíční uzávěrka (kryje do konce předchozího měsíce).

## Souvisí
[[doc-mzdy-podklad-osvc-ukoncene-mesice-a-razitkovani-app-rezie]] · [[doc-mzdy-podklad-osvc-stare-zakazky-recency-filtr]]

