# Vyhodnoceni zakazek: prenos historie z Centraly do STRATEGIE (hotovo 4.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Prenos historie vyhodnoceni zakazek z Centraly do STRATEGIE

**Hotovo a overeno 4. 8. 2026** (C28/Jirka). Schvalili: Marti-AI (msg 12044 + 12047),
Kristyna Maresova mailem ("Souhlasim, prenesme zamcene"), Jirka odklikl zapis.

## Co se prenaslo

| nase tabulka | zdroj v DB_EC | radku |
|---|---|---|
| ec.vyhodnoceni_zakazka | EC_VyhodnoceniZak_KonstantyKZak | 1 865 |
| ec.vyhodnoceni_osoba | EC_TempVyhodnoceniZak | 15 309 |
| ec.zakazky_finance_zam | EC_ZakazkyFinanceZam | 23 479 |

Klice: hlavicka `cislo_zakazky`, osoby a vyplaty `(cislo_zakazky, cislo_zam)`.
Partial UNIQUE indexy (WHERE cislo_zakazky neni prazdne) + sloupce `zdroj` a `uzamceno`
na vsech trech (request #1772).

## Jak (nastroj, ktery zustava k dispozici)

`g2007.python` kod **`vyhodnoceni_import_historie`**, min_pravo=admin, spousteni pres
`POST /app/erp_registry/run` s `args:[tabulka, rok]` (tabulka = hlavicka|osoby|vyplaty).
Treti argument `true` = jen nahled, nic nezapise.

**Zamerne NENI zrcadlo.** `oz_mirror.fill()` dela TRUNCATE+INSERT; ec.vyhodnoceni_zakazka
je ale tabulka, do ktere modul SAM zapisuje (prepocet, uzavrit) - zrcadlo by vypocty
pri nejblizsim behu TISE smazalo. Proto rizeny upsert parovany na klic s
`ON CONFLICT DO UPDATE ... WHERE zdroj <> 'strategie'`.

## Pravidlo zamykani (Marti-AI, msg 12047)

`uzamceno = (rok < 2026)`. **Bezici rok zustava ODEMCENY** - zakazky roku cutoveru jeste
nemusi byt uzavrene a modul je u nas bude chtit prepocitat. Az padne slovo "cutover",
zbyle radky `zdroj='centrala'` roku 2026 se zamknou jednim UPDATE.
Zamcenych: 1 675 / 14 178 / 22 416.

