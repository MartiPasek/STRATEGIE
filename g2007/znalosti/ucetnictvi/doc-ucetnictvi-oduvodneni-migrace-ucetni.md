# Migrace Helios do cloudu a očista účetnictví — proč a co to pro nás znamená

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Migrace Helios do cloudu a očista účetnictví — proč a co to pro nás znamená

*Interní zdůvodnění pro účetní tým · červen 2026*

## Proč to vůbec děláme — nešlo to odložit

Asseco (dodavatel Heliosu) oznámilo **konec podpory SQL Serveru 2019**, na kterém nám běží
produkční databáze. Bez podporované databáze bychom přišli o aktualizace, opravy chyb i
bezpečnostní záplaty — to je u mzdového a účetního systému neúnosné riziko. Museli jsme proto
Helios **přesunout na nový, podporovaný SQL Server (2025)**.

Pro nové prostředí jsme si pronajali dva servery (aplikační + databázový) u CMIS. Migrace na
novou databázi byla nutná tak jako tak — a my jsme toho využili k tomu, aby z ní vzešlo něco
**jednoduššího a přehlednějšího**.

## Příležitost: konečně čisté, rychle uzavíratelné účetnictví

Posledních zhruba sedm let se nedařilo dokončit roční uzávěrku v rozumném čase — účetnictví
zbytnělo balastem, který uzávěrku komplikoval. Rozhodli jsme se proto při migraci provést
**očistu**. Do nové databáze přenášíme záměrně **jen to podstatné**:

- **pouze účetnictví 2025 a 2026** (ne celá historie od roku 2007),
- **bez systému A** (účtování příjemek a výdejek) — tato vrstva se ukázala jako hlavní zdroj
  složitosti a v průběhu roku ji opouštíme,
- **bez zakázek** na úrovni účtování,
- **jediné středisko 001** (základní nastavení Helios).

Cílem je **absolutní jednoduchost a přehled** — účetnictví, které se dá uzavřít rychle a bez
dohledávání.

## Co z Heliosu zůstává

V Heliosu nadále běží to nejdůležitější: **účetní deník a mzdy**. Mzdové výpočty se dál dělají
v Heliosu — ten zůstává oficiálním zdrojem pravdy pro zúčtování.

## Role STRATEGIE — kontrola navíc, ne náhrada

Souběžně s migrací jsme do STRATEGIE **kompletně zrcadlili mzdové podklady za 2025 a 2026** —
mzdový list, mzdové složky, kontace, kalendáře, paušály, srážky, zaručenou mzdu, konfiguraci
zaměstnanců a další. Tato data jsme **přenesli i do nové databáze** a **ověřili 1:1 proti
Heliosu** (počty i návaznosti sedí na řádek).

Co tím získáváme:

- **Kompletní mzdové podklady na jednom místě, na klik** — žádné ruční dohledávání.
- **Nezávislá kontrolní vrstva** — křížová kontrola STRATEGIE × Helios odhalí nesrovnalost dřív,
  než se dostane do uzávěrky.
- **Příprava na hladší uzávěrku** — podklady jsou připravené a ověřené předem.

## Co se pro účetní tým NEMĚNÍ

- **Mzdy se dál počítají v Heliosu** — zůstává zdrojem pravdy pro zúčtování.
- **Účetní mají finální dohled a profesní odpovědnost** za uzávěrku — STRATEGIE je nástroj
  kontroly a přípravy, ne náhrada úsudku.
- **Legislativní správnost zůstává zachována.**

## Shrnutí

Migraci si vynutil konec podpory SQL 2019. Využili jsme ji k očistě, která účetnictví
**zjednoduší a zrychlí uzávěrku**, a zároveň jsme přidali **nezávislou kontrolní vrstvu** s
kompletními, ověřenými mzdovými podklady. Pro každodenní práci to znamená méně balastu, rychlejší
uzávěrku a jistotu, že čísla sedí.


