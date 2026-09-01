# Ruční přepis papírového docházkového výkazu — kam to patří a tři pasti

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Ruční přepis papírového docházkového výkazu

> oblast dochazka · Jirka (C-28) + Claude, 1. 9. 2026 · ověřeno naostro na srpnu 2026 u dvou lidí

## Proč to vůbec je

Lidem, kteří mají vypnutý docházkový terminál i mobilní aplikaci (typicky úklid na dohodu),
se hodiny píší na papír a někdo je pak musí přepsat do systému. Papír má hlavičku
(jméno, osobní číslo, úvazek), pak sloupce příchod, odchod, přestávka, odpracováno, poznámka.

## Kam se to zapisuje — DVĚ tabulky, ne jedna

1. **tenant.att_entry** — docházka, jeden řádek na každý souvislý úsek.
   Vyplň `entry_date`, `started_at`, `ended_at`, `hours` (rozpětí úseku), `entry_type_id`,
   `status` = pending, `source` = manual, `is_active` = false, `project_ref`.
   `user_id` a `firma_id` doplní spouštěče samy, nevyplňuj je.
2. **tenant.vyroba_work** — rozpad s **druhem činnosti**, jeden řádek na každý pracovní úsek.
   Váže se přes `att_entry_id`. Bez něj v docházce chybí činnost a nikde to nenahlásí chybu.
   Druh činnosti je v `tenant.vyroba_cinnost` (sloupec `ec_cislo` = číslo činnosti ze staré
   Centrály, například 124 = Úklid firmy).

**Typ záznamu i činnost vždy opiš z vlastní historie toho člověka**, ne z úvahy — přečti si
jeho starší řádky a použij stejný `entry_type_id`, `project_ref` a `cinnost_id`. Jinak se mu
měsíce rozejdou a například ve financích zakázek bude půl roku pod jedním označením a půl roku
pod ničím.

## Tři pasti, na které jsem narazil

**1. Sloupec `break_minutes` se nikde nečte.** V srpnu 2026 byl prázdný u všech 4773 řádků
a funkce `tenant.att_den_hodiny` ho vůbec nebere. Přestávka se vede jako **samostatný úsek**
typu break (v srpnu jich bylo 1246). Papírový den s přestávkou uprostřed proto rozděl na tři
řádky — práce, přestávka, práce. Kdo napíše jeden dlouhý úsek a přestávku dá do `break_minutes`,
připíše člověku hodiny navíc a nic to nenahlásí.

**2. Spouštěč v databázi počítá jinak než automat.** `tenant._att_resummary_one` (spouštěč
`att_entry_resummary` nad att_entry) sčítá jen typy work, homeoffice a fond_doplneni — **režii
ne**. Čistě režijní den u něj vyjde 0 a když pro ten den souhrn ještě neexistuje, nezaloží se
vůbec. Správnou hodnotu doplní až automat `sync_ec_dochazka_sumaden` (běží každých 10 minut,
počítá přes `att_den_hodiny`, která režii bere). **Po zápisu tedy počkej na automat a teprve
pak kontroluj denní souhrn** — nulu hned po zápisu neber jako chybu. V srpnu 2026 mělo čistě
režijní dny 9 lidí.

**3. Rozpad se sám nedoplní.** Rozpad s činností dřív zakládal přenos ze staré Centrály
(`source_system` = centrala1), a ten je od 30. 7. 2026 vypnutý. U ručního zápisu ho musíš
založit sám; jako `source_system` použij existující hodnotu manual_fix.

## Postup, který se osvědčil

1. Sken přečti ve **vysokém rozlišení po částech** — ručně psané číslice se v náhledu celé
   stránky čtou špatně. U každého dne ověř, že příchod, odchod a napsaný součet sedí dohromady.
2. **Nejasné místo (kaňka, škrtnutí) nehádej** — zeptej se zadavatele.
3. Pozor na zápis součtu: lidé píší hodiny a minuty ve tvaru `3,57`, což znamená
   3 hodiny 57 minut, **ne 3,57 hodiny**. Do databáze patří desetinné číslo (3,95).
4. Zápis dělej s pojistkou `WHERE NOT EXISTS` na dvojici zaměstnanec a čas začátku,
   ať se dvojím spuštěním nezaloží duplicity.
5. Po zápisu ověř čtením a **porovnej součet měsíce proti papíru**.
6. Zkontroluj, že přepočet nerozhodil nikoho jiného — porovnej docházku proti dennímu souhrnu
   u všech lidí před zápisem i po něm. Rozdíly odpovídající placené absenci jsou v pořádku.

## Co ověřit předem

- Je měsíc v `tenant.att_period_lock`? Zamčený měsíc přepočet odmítne a hodiny se do mezd
  nedostanou.
- Nemá už ten den záznam z jiného zdroje (tablet, appka)? Pak se ptej, jestli přepsat, nebo nechat.

