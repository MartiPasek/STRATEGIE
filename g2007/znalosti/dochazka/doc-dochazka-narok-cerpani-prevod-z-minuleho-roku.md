# Převod z minulého roku (D / DN / SD) se zadává přímo v Nároku a čerpání (Peťa 9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 9. 9. 2026**, konzultováno s Týnkou. Spouštěč — Michaela Hladíková měla sick days přečerpané o půl dne, protože jí chyběl převod z minulého roku, a nebylo kde ho zapsat.

## Kde to žije — ŽÁDNÉ NOVÉ MÍSTO

`tenant.dovolena_korekce` (existující tabulka ručních korekcí nároku, vedená po rocích a po lidech, s důvodem a podpisem) dostala tři sloupce:

`prevod_d_dny` · `prevod_dn_dny` · `prevod_sd_dny` — ve DNECH, smí být i záporné (když člověk dny naopak dluží). K tomu `updated_at` a `upravil`.

Je to totéž jako dosavadní `presun_do_dn_dny` — ruční zásah do nároku pro konkrétní rok. Zakládat vedle toho druhou tabulku by znamenalo dvě místa na tutéž věc.

## Pravidlo

**Nárok = to, co je v Podmínkách, PLUS převedeno.** Promítne se do všeho ostatního — zbývá, obě „vše" kolonky i do hlídání stropu při žádosti (`att_narok_osoba` čte z téhož výpočtu).

**Hodnota platí vždy jen pro svůj rok.** Do dalšího roku se nic nepřenáší samo — v roce 2027 budou políčka prázdná, dokud tam někdo nezapíše, co se převádí z 2026. Peťa 9. 9.- *„platit by to mělo vždy pro ten daný rok."*

## Kdo smí zapisovat

Peťa- *„skupinu novou dělat nebudeme, udělej to jako kdo vidí do celé té obrazovky."*

Zapisovat smí ten, kdo **není omezený působností** v `tenant.att_fix_scope` — má `fix_all`, `scope` je `vse` nebo prázdný, nebo v tabulce vůbec není. Prakticky- **Peťa, Michelle, Jirka, Šárka, Týnka ano; Dušan a Michaela ne** (vidí jen výrobu). Ověřeno v datech 9. 9. 2026. Žádný seznam osobních čísel v kódu — ty se v docházce ruší.

## Kde se to zadává

Tři poslední sloupce přehledu **převedeno D / DN / SD (dny)**. Hodnota se uloží po opuštění políčka nebo Enterem, políčko blikne zeleně a přehled se přepočítá. Ukládá se s časem, podpisem a důvodem — ten se vyplní sám jako „převod z roku <předchozí>", pokud řádek ještě žádný nemá.

## Kód

- `att_narok_cerpani` — načítá `prevod_*` a přičítá je k nároku; vrací je v řádcích a přidává klíč `muze_prevod` (podle působnosti), aby stránka věděla, jestli kreslit políčka.
- **`att_narok_prevod_save`** (nový, `g2007.python`) — samotný zápis- kontrola práva, rozsahu (max 400 dnů) a tvaru čísla, pak UPSERT na `(tenant_id, cislo_zam, rok)`.
- `modules/erp/api/dochazka_zak_tab.py` — tenký delegate `POST /app/dochazka-narok/prevod`.
- `apps/api/static/dochazka-narok.html` — políčka, uložení, hlášky. Tenhle soubor **žije v gitu, ne v `g2007.soubor`**, takže se mění deployem.

Ověřeno naostro- prázdné číslo člověka, cizí sloupec, text místo čísla i hodnota 999 se odmítnou s českou hláškou a stavem 400.

## Co zbývá

Peťa chce ještě dořešit, jak v přehledu ukázat **aktuální a minulý rok vedle sebe**, jak to měla Centrála („dovolená aktuální" / „dovolená minulý rok"). Data na to jsou — každý rok má v tabulce svůj řádek. Připomínka naplánovaná na pondělí 14. 9. 2026.

