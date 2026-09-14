# Inventář — STRATEGIE Mobil

> Pořídil Claude-28, 14. 9. 2026. Seznam je **vytažený z běžící aplikace**
> (`window.__M2W.SCREENS` na živém `/mobile`), ne z kódu na disku.

---

## Kde co žije (technický průzkum)

| Co | Kde to je | Jak se to mění |
|---|---|---|
| **Obsah aplikace** (obrazovky, tlačítka, logika) | databáze, tabulka `g2007.soubor`, 31 dílků `apps/api/static/mobile_parts/*` | úprava dílku + publikace |
| **Složená stránka**, kterou telefon stáhne | `g2007.soubor`, artefakt `apps/api/static_db/mobile.html` (1,13 MB) | vzniká publikací |
| **Vzhled** | jediný dílek `02_styles.html` (13,7 kB) — ale **jen z části** | tamtéž |
| **Zbytek vzhledu** | **2 702 míst zapsaných přímo u prvků** v ostatních dílcích | jen v tom konkrétním místě |
| **Seznam dlaždic** | databáze `public.mobile_app_dlazdice` (69 aktivních) | v datech, ne v kódu |
| **Obal aplikace** | `APP/Mobile` (Android, Kotlin), `APP/iOS` (Swift) | běžný git + vydání do obchodu |

**Android i iPhone stahují tutéž stránku ze serveru** — obsah se mezi platformami rozejít
nemůže. Rozejít se může jen obal (notifikace, ikona, spodní pruh).

**Žádný design systém neexistuje.** Ve stylech je 14 pojmenovaných hodnot (barvy, jedna
výška lišty); všechno ostatní je zapsané ad hoc u jednotlivých prvků.

---

## Kolik toho je

| | počet |
|---|---|
| obrazovek v aplikaci | **127** |
| z toho nafoceno a použito pro návrh | **20** |
| dlaždic v rozcestníku (aktivních) | **69** (67 s emoji, 2 s obrázkem) |
| dílků obsahu v databázi | **31** |
| různých emoji v roli ikon | **198** |

---

## Dvacet obrazovek použitých pro posouzení návrhu

Vybrané podle **skutečného používání**: docházka je nejvytíženější část systému
(5 092 zápisů z mobilu za 30 dní od 57 lidí), zbytek podle toho, kam vedou hlavní vstupy
ze spodní lišty. **Analytika po obrazovkách v systému není** — ověřeno, že žádná tabulka
otevření obrazovek nevede a `fw.dbg_req` je za posledních 30 dní prázdná.

| # | Obrazovka | Jak vypadá | Stav zachycený na snímku |
|---|---|---|---|
| 1 | Domů (`home`) | úvod, nápis + fotka | běžný |
| 2 | Docházka (`dochazka`) | rozcestník s dlaždicemi + START | rozpracovaný den |
| 3 | Moje docházka (`moje_dochazka_b`) | seznam dnů | plný |
| 4 | Moje absence (`moje_absence`) | formulář + seznam žádostí | plný |
| 5 | Nemocenská (`sick`) | text + akce | **prázdný** |
| 6 | Plán (`plan`) | roční přehled + postranní volby | plný |
| 7 | Požádat o opravu (`doch_oprava_zadost`) | dlouhý seznam dnů | plný |
| 8 | Moje podmínky (`moje_podminky`) | tabulka hodnot | plný |
| 9 | Aplikace (`apps`) | tři záložky, mřížka dlaždic | téměř prázdný |
| 10 | Firma (`firma`) | novinky s tlačítky | plný |
| 11 | Úkoly (`notifs`) | seznam upozornění | plný |
| 12 | Moje TODO (`mytodo`) | zadání + seznam | **prázdný** |
| 13 | Kdo kde dnes (`kdekdo`) | dlouhý seznam lidí + filtr | plný (82 lidí) |
| 14 | Nastavení (`settings`) | dvanáct řádků | plný |
| 15 | Moje osobní údaje (`hr_me`) | dlouhý formulář | plný |
| 16 | Vedení firmy (`vedeni`) | čísla + skupiny dlaždic | plný |
| 17 | Kontakty (`contacts`) | jen vysvětlující věta | **prázdný** |
| 18 | Moje hodiny (`moje_hodiny`) | hlavička + vysvětlení | **bez dat** |
| 19 | Moje finance (`moje_finance`) | zámek na PIN | **zamčený** |
| 20 | Lísteček od lékaře (`med`) | text + akce | **prázdný** |

Mezi nimi jsou **čtyři prázdné stavy, jeden zamčený, dva formuláře, tři dlouhé seznamy
a dva rozcestníky** — tedy všechny podoby, které v aplikaci existují.

---

## Zbývajících 107 obrazovek

Nejsou nafocené. **Vzhled se jich přesto týká úplně stejně** — mění se totiž společné
prvky (písmo, barvy, ikony, karty, tlačítka), ne jednotlivé obrazovky.

Rozdělení podle toho, která ikona spodní lišty se u nich rozsvítí:

| Sekce | Počet | Příklady (jména zkratek z kódu) |
|---|---|---|
| **Aplikace** (rozcestník všeho ostatního) | 98 | `hr_*` personalistika (24), `bk_*` rozvrh školy (9), `kara_*` (7), `set_*` nastavení (9), `migrace_*`, `martinky_*`, `cil_*`, `ops`, `coord`, `fronta`… |
| **Docházka** | 14 | `absence`, `moje_volno`, `doch_opravy`, `doch_opravy_den`, `cesta_vyber`, `med`, `sick`… |
| **Domů** | 2 | `home`, `exec_approval` |
| **Úkoly** | 4 | `notifs`, `claudetasks`, `claudeDetail`, `strtask` |
| **Firma** | 2 | `firma`, `vyroba` |
| bez zařazení | 7 | mimo jiné `moje_dochazka_b` |

> ⚠️ **Co u těch 107 netvrdím:** jejich česká jména ani stavy. Neotevřel jsem je —
> šlo by o dohad. Zkratky výše jsou z kódu, ne názvy, které uvidí uživatel.

---

## Stavy, které se špatně vyvolávají

Prázdné a chybové obrazovky bývají vizuálně nejzanedbanější, proto jsou v náhledech
čtyři z nich. **Chybový stav (spadlé spojení, chyba serveru) se mi vyvolat nepodařilo**
a nemám ho tedy nafocený — je to jediná díra v inventáři a přiznávám ji.
