# Co ve STRATEGII reálně vzniká od lidí - měření za 30 dní (8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Co ve STRATEGII realne vznika od lidi

**Zmereno 8. 9. 2026** (Claude-24 / Kristy) na otazku *"jedine, co se zapisuje primo ve strategii,
je dochazka - muzes to overit?"*. Odpoved: **skoro ano, jsou to dve veci.**

Doplnuje princip z [[doc-dochazka-jeden-zdroj-pravdy]] o **cisla misto dojmu**.

## Merenі za 30 dni (stav k 8. 9. 2026)

| tabulka | zdroj radku | radku |
|---|---|---|
| `tenant.att_entry` | `mobile_app` (pichacky) | 5 209 |
| | `manual_fix` (opravy dochazky) | 407 |
| | `absence_req` (zadosti o absenci) | 300 |
| | `automat` + `notif_confirm` | 489 |
| | `source_system='centrala1'` | **13** |
| `tenant.vyroba_work` | `app` (rozpad hodin na zakazky) | 3 040 |
| | `manual_fix` | 53 |
| | `sync` + `import` z Centraly | 93 |
| `tenant.wage_movement` | `import_src='EC_PRIPL'` | **150 - vse z Centraly** |
| `ec.vyhodnoceni_zakazka` | `zdroj='centrala'` | 1 864 |
| | `zdroj='strategie'` | **1** (zkouska C28) |
| `tenant.zakazka_meta` | celkem v tabulce | **2** |

## Zavery

1. **Lide u nas vytvareji dve veci: dochazku a rozpad hodin na zakazky.** Nic jineho.
2. **Priplatky a srazky se porad zadavaji v Centrale** - za 30 dni u nas rucne nevznikl ani jeden
   radek, vsech 150 pritekle importem. To je take duvod, proc cutover do Prahy (rozhodnuti Marti
   27. 7. 2026) porad visi - viz [[doc-mzdy-priplatky-srazky-cutover-praha]].
3. **Modul Vyhodnoceni zakazek jeste neni v ostrem provozu** - jediny radek se `zdroj='strategie'`
   je Jirkova zkouska ze srpna.
4. Pro rozhodovani "zrcadlo nebo nase tabulka" plati: **kdyz se do tabulky u nas nepise, je to
   zrcadlo.** Naopak nase tabulka jen tam, kde zapis u nas realne existuje - jinak vzniknou
   napul otevrene dvere a z nich dvoji zdroj pravdy.

## Poznamka k mereni

Merilo se pres `source` / `source_system` / `import_src` / `zdroj` a `created_at > now() - 30 dni`.
`pg_stat_all_tables` se na tuhle otazku **nehodi** - u zrcadel ukazuje miliony INSERTu ze syncu
(napr. `tenant.oz_zakazky` ma 5,7 mil. ins pri 5 696 zivych radcich, protoze job `oz_sync_all`
kazdych 30 minut dela TRUNCATE+INSERT). Provoz zrcadel prehlusi vse ostatni.

**Neoverovano:** HR karty, ukoly, maily a dokumenty - tam se take neco zadava. Mereni pokryva
domenu zakazky / mzdy / dochazka / vyhodnoceni.

