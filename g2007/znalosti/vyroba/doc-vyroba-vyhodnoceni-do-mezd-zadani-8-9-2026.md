# Vyhodnocení zakázek → mzdy: rozhodnutí a poslední chybějící článek (8. 9. 2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Vyhodnoceni zakazek -> mzdy

**Zadani upresneno 8. 9. 2026** (Kristy + Claude-24). Navazuje na modul C28/Jirky, ktery je
funkcne hotovy - viz [[doc-vyroba-vyhodnoceni-zakazek]] a [[doc-vyroba-vyhodnoceni-zakazek-stav-4-8-2026]].
Podrobny technicky handoff: soubor `C24_Vyhodnoceni_zakazek_HANDOFF_do_mezd_2026-09-08.md`.

## Rozhodnuti (nediskutovat znovu)

1. **Dusan spousti uzaverku ve STRATEGII**, ne v Centrale.
2. Hodiny pro premie = **`tenant.vyroba_work`**, ne `att_entry` - jeden zaznam dochazky se deli
   na vic zakazek, takze `att_entry` je na tohle spatna granularita.
3. Odmena patri do **mesice, kdy byla zakazka uzavrena**.
4. Radky do mezd se zapisuji rovnou jako **`approved`** (viz duvod nize).

## Co chybi - jediny clanek

`ec.vyhodnoceni_uzavrit` uz zapisuje vysledek do `ec.zakazky_finance_zam` (`fix_premie`,
`vyplatit`, `pocet_hodin`, `hod_sazba`). **Nic to ale neprenese do `tenant.wage_movement`**
(typ 67 = `odmeny_finance_zakazek`, `ec_typ_id=50` -> mzdova slozka 651).

Reseni: nova funkce `ec.vyhodnoceni_do_mezd(p_zak)` + akce `do_mezd` ve whitelistu
`modules/erp/api/vyhodnoceni_actions.py`, zarazena do `_EC_AKCE_S_OPRAVNENIM` - tim automaticky
zdedi opravneni z `ec.akce_opravneni` i audit do `ec.akce_audit`.

**Krok nula:** `ec.vyhodnoceni_uzavrit` do `zakazky_finance_zam` NEPLNI `zdroj` ani `datum_porizeni`,
prestoze oba sloupce existuji. Bez nich nepoznáme, co vzniklo u nas, a nefunguje pojistka proti
dvojimu zapoctu. Doplnit `zdroj='strategie'`, `datum_porizeni=now()`.

## PAST, kterou je nutne vyresit prvni: firma EC vs ES

`wage_movement.engagement_id` je pracovni **pomer**, a jeden clovek muze mit pomer ve dvou firmach
(doctrine #24). Kontrolni cislo za 7/2026 se deli na **EC 9 radku / 2 990 Kc + ES 38 radku / 8 880 Kc**,
tedy odmeny vznikaji v obou firmach. Import z Centraly firmu zna, **nase cesta ji zatim neresi.**

`ec.vyhodnoceni_uzavrit` sice `engagement` joinuje, ale s `LIMIT 1` a jen kvuli zjisteni, zda je
clovek HPP (koeficient 1,4 vs 1,0). Tam je `LIMIT 1` neskodny - **pro vyber pomeru, na ktery se
povesi penize, neskodny NENI.** Jinak odmena spadne do spatne firmy.

## Proc `approved` a ne `pending`

Schvalovaci kolecko existuje (`draft` -> `pending` -> `approved` -> `exported`, endpoint
`/app/pripl/workflow`, schvaluje drzitel postu s `wage_approver`) - viz
[[doc-mzdy-priplatky-srazky-schvalovani-a-zkusebni-rezim]]. **Dnes ho ale nikdo nepouziva:**
`pending` ma nula radku, `approved_by_id` je vyplnene u nuly radku, vse chodi importem z Centraly
rovnou jako `approved`. A zapis pres formular je zamceny cutoverem, ktery od 1. 8. visi.
Proto `approved`; az se cutover dotahne, prepnuti je zmena jedne hodnoty.

## Pojistka proti dvojimu zapoctu (tri vrstvy)

1. `import_src='STRATEGIE_VYH'` + `import_src_id` = id radku `zakazky_finance_zam`, `ON CONFLICT DO NOTHING`.
2. Kontrola, ze pro tutez osobu, obdobi a zakazku uz neleží radek typu 67 s `import_src='EC_PRIPL'`
   - pokud ano, **preskocit a nahlasit ve vysledku, ne tise zahodit**.
3. Stara dochazkova cesta `mzdy_finance_zakazek_rows` zustava vypnuta.

Zapis jde mimo `_pripl_write_guard` (je to strojovy import jako `sync_priplatky_from_ec`),
takze bezpecnost stoji vyhradne na temhle trech pojistkach a na opravneni u tlacitka.

## Overeni pred ostrym srpnem

Spocitat retez za 7/2026 a porovnat na **47 radku / 11 870 Kc**. Testovat na NEuzamcene zakazce -
historie z Centraly (1 675 zakazek 2021-2025, `uzamceno=true`) je chranena tvrdym zakazem
primo v `ec.vyhodnoceni_uzavrit`.

