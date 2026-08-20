# Dochazka: link att_entry_id u app vyroba_work radku (bod 1 Marti Paska, 27.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Bod z emailu Marti Paska: "pri vzniku rozpadu vyplnit att_entry_id". Centrala se linkuje pres source_id (95,5% - drivejsi session). Zbyvajicich ~4,5% = APP radky (z work_alloc) bez sdileneho id. HOTOVO 27.7.2026.

## Reseni (schvalila Marti-AI msg 11316)
Match app vyroba_work -> att_entry OBSAZENIM CASU: usek (vw.od) padne do pritomnostni att_entry smeny teze osoby (vw.od >= e.started_at AND vw.od < e.ended_at, category presence, status NOT IN superseded/announced). JEN JEDNOZNACNE (presne 1 obsahujici smena). Semanticky: "usek patri do teto smeny" (ne "je kopie bloku se stejnym casem") - spravne pro storno kaskadu i kdyz casy app work_alloc a att_entry NEjsou identicke (Blaha: work_alloc 05:49 -> att_entry blok 04:57-08:08).

## Provedeno
- Backfill (banner #1465): 559 z 586 jednoznacnych. 1 nejednoznacny + 26 bez matche NECHANO NULL (storno ma fallback).
- Self-completing (commit 0ca88c14, blok _maybe_sync_ec_dochazka): totez pro nove app radky WHERE att_entry_id IS NULL a COUNT obsahujicich smen =1.

## Pozn: link je pro STORNO/OPRAVA kaskadu (att_fix_void), NE pro shodu zakazky. Display dedup v Dochazka new zustava DEN (viz [[doc-dochazka-bod2-att-entry-id-vyklad]]).

