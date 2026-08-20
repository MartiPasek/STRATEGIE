# Zakazky: priprava helios_id (Zakazka_ID) pro Helios prechod (bod 9 Marti Paska, 27.7.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Bod z emailu Marti Paska 26.7.: "do budoucna nahradime CisloZakazky fieldem Zakazka_ID (vazba pres id, ne cislo) - at uz ty fieldy existuji." Additivni PRIPRAVA. HOTOVO 27.7.2026 (i28).

## Zdroj Helios ID
tenant.oz_zakazky."ID" (integer, velbloudi+uvozovky!) = Helios TabZakazka.ID. Cislo->ID je UNIKATNI (zadne cislo nema vic ID).

## Provedeno (schvalila Marti-AI msg 11295: jen zakazka + vyroba_work; att_entry/ec_zakazka_prehled az 2. vlna)
- ALTER: tenant.zakazka ADD helios_id integer; tenant.vyroba_work ADD zakazka_helios_id integer (banner #1455).
- Backfill z oz_zakazky."ID" pres shodu cisla (trim): zakazka 416/417 (1 bez paru = spec. kod), vyroba_work 13609/13609 (100%).
- Self-completing (commit a17d04ef, blok _maybe_sync_ec_dochazka): dopocita helios_id pro nove radky WHERE IS NULL.

## Klicovani ZUSTAVA na cisle. helios_id = additivni atribut pro budoucnost, zadna zmena FK/joinu. POZOR nazvy: oz_zakazky."ID"/"CisloZakazky" velbloudi s uvozovkami; zakazka.cislo, vyroba_work.zakazka_ref lowercase.

