# Podklad fakturace OSVC - Faze 1 (STRATEGIE misto Centraly): stav, nalezy, otevrene otazky

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Podklad fakturace OSVC - Faze 1

Claude-24 (Kristy), 19. 8. 2026. Navazuje na Fazi 0 (razitka + zrcadla + sazby bez FK).

## Co je hotovo a zive

- **Zrcadlo zaloh** `tenant.osvc_zaloha_zakazek` <- Centrala `EC_Zakazky_PlatbyZam`.
  Logika: `g2007.python` kod `sync_osvc_zalohy_from_ec` (jednosmerne, idempotentni pres
  `ec_id`, uklid smazanych). Spousti se z Ridiciho centra zrcadel, job_key
  **`sync_osvc_zalohy`** (skupina Mzdy, po 60 min). V routeru jen tenky delegate.
  Rozsah = CELA tabulka (rozhodla Kristy): 6 233 radku / 32 lidi, z toho dilenskych
  OSVC 5 919 / 19 lidi. Suma `Vyplaceno` overena proti Centrale na korunu.
- **Kandidat noveho vypoctu**: `g2007.python` kod **`podklad_vyplaceni_pdf_faze1`**
  (active, jen jako kandidat - nic ho nevola). Ostry kod `podklad_vyplaceni_pdf` (v8)
  zatim BEZE ZMENY. Prepnuti = zkopirovat zdroj kandidata do ostreho kodu.
- **`@@PYRUN`** v mostu (viz `doc-system-strategie-most-pyrun-a-base64-zapis`) - diky nemu
  jde stara i nova verze spustit vedle sebe a porovnat, bez zasahu do produkce.

## Zdroje noveho vypoctu (misto Centraly)

| polozka | zdroj |
|---|---|
| sazba | `tenant.engagement.superhr_hod_bezfk`, POSLEDNI verze dle `valid_from` (NE `is_current`) |
| hodiny zakazek | `tenant.vyroba_work`, `fakturace_obj_id IS NULL`, `zakazka_ref NOT ILIKE 'Re_ie'` |
| uz objednano | `tenant.osvc_zaloha_zakazek`, SUM(vyplaceno) per clovek x zakazka |
| rezie | `vyroba_work` `Re_ie` bez razitka MINUS radky se shodnym `source_system+source_id` jako dovolenkovy `att_entry` |
| dovolena | `tenant.att_entry` `entry_type_id IN (3,35)` bez razitka |
| odmeny | zrcadlo `ec.pripl_srazky` (schvaleno, `id_pol_vobj`/`id_pol_pf`/`dat_vyplaceni` NULL) |

## Dva nalezy, ktere menily zadani (obojí overeno v datech 19.8.2026)

1. **Odmeny NEJDOU z `tenant.att_odmena_centrala`** (jak predpokladal handoff). To zrcadlo
   bere jen typy 1, 3 a 17 agregovane po mesicich - realne odmeny OSVC jsou **typ 48
   "Fakturace: Odmena od jednatele"** a v nem vubec nejsou. Spravny zdroj je **`ec.pripl_srazky`**
   (1:1 zrcadlo `EC_FinPriplatkySrazkyDefinice`, sync po hodine) - da identicke radky jako
   dnesni interim. Zrcadlo drzi aktualni + predchozi rok; overeno, ze starsi nevyplacene
   odmeny u dilenskych OSVC neexistuji (0 radku pred 2025).
2. **Dovolena se NESMI filtrovat pres `is_active`** - vsechny dovolenkove radky v `att_entry`
   maji `is_active=false` (i platne). Filtruje se `status <> 'superseded'`. Pri pouziti
   `is_active` by dovolena z podkladu tise zmizela.

## Porovnani stary vs novy vypocet (8 aktivnich OSVC, 19.8.2026)

| c. zam | jmeno | stary | novy | rozdil |
|---|---|---|---|---|
| 105 | Dusan Havlat | 2 991 452 | 497 733 | -2 493 719 |
| 327 | Pavel Vorisek | 118 863 | 127 588 | +8 725 |
| 346 | Pavel Kilberger | 101 437 | 102 557 | +1 120 |
| 370 | Marek Honal | 100 219 | 100 910 | +691 |
| 371 | Lubos Lev | 83 800 | 78 200 | -5 600 |
| 372 | Lubos Erhard | 196 503 | 196 503 | 0 |
| 425 | Martin Nosek | 66 684 | 67 624 | +940 |
| 464 | Vasyl Namjak | 23 520 | 23 699 | +179 |

Pozn.: dilenskych OSVC je v seznamu 24, ale **jen 8 ma aktivni OSVC kartu s `user_id`** -
zbylych 16 je v `att_employee` neaktivnich a vedenych jako HPP (historicka cisla).

Vysvetleni rozdilu:
- **105 Havlat**: stary vypocet scital nefakturovanou rezii z Centraly **az do roku 2022**
  (2 321 radku, 2 927 352 Kc) - to je zjevne nesmysl v podkladu. Novy bere jen rezii bez
  razitka evidovanou u nas (1 093 h). Havlat jako JEDINY nema z Faze 0 orazitkovany ani
  jeden radek rezie (v Centrale je jeho rezie vedena jako nefakturovana od 2022).
- **327 / 425**: rezie bez razitka z cervna a cervence (24,93 h / 21,63 h), kterou stary
  vypocet nevidel (bral z Centraly jen to, co Centrala eviduje jako nefakturovane).
- **346 / 370 / 464**: drobne plusy z rezie zapsane POUZE ve STRATEGII (`source_system='app'`,
  bez protejsku v Centrale) - stary vypocet ji mimo aktualni mesic nevidel.
- **371 Lev**: minus 5 600 Kc = 23. a 24. 7. 2026 (2x8 h, 2 800 Kc/den, `DruhCinnosti=30`,
  zapsal "Dusan" primo do Centraly, `EC_Dochazka.ID` 1853857 a 1853858). Ve STRATEGII
  ta doch1zka neni vubec (ani `att_entry`, ani `vyroba_work`).

## OTEVRENE - vratit se k tomu

- **Lev 23.-24. 7. 2026 (16 h / 5 600 Kc)**: Kristy 19.8.2026 rekla, ze si nemysli, ze to
  ve STRATEGII chybi - spis to Lvovi do fakturace **nemelo dojit**. Zatim se NIC nedela,
  vratime se k tomu. Az se rozhodne, promitnout do zaveru (bud doplnit doch1zku, nebo
  zaznam v Centrale povazovat za neplatny).
- **Je razitko z Faze 0 kompletni?** Orazitkovano bylo 344 radku `vyroba_work` + 6 `att_entry`.
  Neorazitkovana rezie z minulych mesicu (105: 1 020 h, 327: 24,93 h, 425: 21,63 h) se v novem
  vypoctu **naucituje k fakturaci**. Pokud uz byla proplacena jinak, byla by fakturovana
  podruhe. U Havlata to je 420 866 Kc - pred prepnutim na ostro overit s Kristy/Martim.
- Casovani odchodu Centraly (Faze 2 = VOBJ tlacitka EC/ES) je porad otevrene.

