# Nastroje Marti-AI: DB_ST bezi na EC-SERVER2, ne v Praze - vzdy si nech potvrdit, ktery stroj odpovedel (6.9.2026)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Nastroje Marti-AI: over si, ktery stroj opravdu odpovedel

**Zjistil:** Claude-28 (Jirka Honomichl), 6. 9. 2026 vecer, pri overovani disku serveru.

## Co se stalo

Potreboval jsem zjistit, jestli na **prazskem databazovem serveru EUR-DB-MSSQL-1P
(10.200.188.12)** fyzicky existuji disky E a F. Marti-AI sama navrhla cestu: spustit
`EXEC xp_fixeddrives` pres svuj nastroj `eurosoft_strategie_query_raw` (databaze `DB_ST`).

Vysledek vypadal duveryhodne — vratil dva disky s volnym mistem. **Byl ale z jineho stroje.**
Cisla (C 84 768 MB a D 268 047 MB, tedy 82,8 GB a 261,8 GB) presne sedela na **plzensky
EC-SERVER2**, jehoz hodnoty jsem cetl deset minut predtim. Prazsky databazovy server ma
v tu chvili C 39,7 GB a D 147,5 GB.

Potvrzeno dotazem `SELECT @@SERVERNAME`: nastroj odpovida z **`EC-SERVER2\SQLEXPRESS2017`**.

## Co si z toho vzit

- **`eurosoft_strategie_query_raw` (DB_ST) bezi na plzenskem EC-SERVER2**, ne na 188.12.
  Totez plati pro SQL most s `db=mssql` — take odpovida `EC-SERVER2\SQLEXPRESS2017`.
- **Na SQL na 10.200.188.12 nema pristup ani Marti-AI, ani most.** Marti-AI ma exec jen
  na dva stroje: `praha_exec` (EUR-APP-1P, 188.11) a `plzen_exec` (EC-SERVER2).
- **Nazev databaze ani nazev nastroje nerika, na kterem stroji bezi.** Kdyz na odpovedi
  zalezi, zeptej se rovnou `SELECT @@SERVERNAME` a porovnej s tim, co jsi cekal.
- Marti-AI si nastroje k databazim **plete opakovane** — tyz vecer poslala prikaz
  pro PostgreSQL (`fw.disk_monitor`) na MSSQL a dostala „Invalid object name".
  Nebylo to skodlive, ale ukazuje to totez: **overuj, kam to opravdu slo.**

## Jak se to poznalo

Ne z chybove hlasky — ta zadna nebyla. **Poznalo se to podle cisel, ktera nesedela
k ocekavanemu stroji.** Kdyby cisla byla podobna, prosla by chybna odpoved jako platna.
Proto: u kazdeho dotazu, ktery ma rozhodnout o zasahu, si nech potvrdit i **identitu zdroje**,
ne jen vysledek.

