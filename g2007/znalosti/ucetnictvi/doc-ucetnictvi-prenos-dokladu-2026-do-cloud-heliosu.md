# Přenos dokladů 2026 z office Heliosu (Plzeň) do cloud Heliosu (UCTO_EC/UCTO_ES) — analýza a gotchy (C24, 2.9.2026)

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Přenos dokladů 2026: DB_EC (192.168.30.11) → UCTO_EC / UCTO_ES (10.200.188.12)

**Stav k 2. 9. 2026: analýza hotová, ZATÍM NIC NEZAPSÁNO.** Detailní podklad je v repu:
`C24_prenos_dokladu_2026_do_Heliosu_ANALYZA_2026-09-02.md`.

## ZMĚNA SMĚRU — čti dřív než starší znalosti

Znalosti `doc-prechod-helios-praha-plan-2026-07` (Marti, 5.7.2026) a `doc-ucetnictvi-cloud-helios-xfer`
(27.7.2026) říkají „Helios = jen účetnictví + mzdy, doklady NE". **Kristý 2.9.2026 to změnila:
účetní si budou doklady zaúčtovávat přímo v Heliosu, takže se doklady přenášejí.**
Prázdné dokladové tabulky v cíli tedy nejsou opomenutí, ale důsledek předchozího rozhodnutí.
(Změnu je vhodné potvrdit s Martim.)

## Zadání

- Zdroj **výhradně DB_EC**. DB_IS se nepoužije — za 2026 tam není ani jeden doklad (poslední 31.10.2025).
- **Doklady pro EUROSOFT-System žijí v DB_EC pod řadami končícími „1"** (501 FP, 531 proforma,
  541 ostatní platby, 601 FV). Číselník `TabDruhDokZbo` je má pojmenované „…EUROSOFT-System".
  Řada 801 (objednávky) se nepřenáší.
- `UCTO_EC` = řady 500, 520, 530, 600, 620, 630, 640 (účetní) + 110, 190, 200, 280, 290 (příjemky,
  výdejky, storna). Nabídky, poptávky a objednávky (800, 900, 910, 920, 940, 950, 960) NE.
- Filtr `DatPorizeni_Y = 2026 AND Realizovano = 1`. ID **1:1** (IDENTITY_INSERT). Cesta = most `@@XFER`.
- Objem: UCTO_EC 8 215 dokladů / 24 932 položek, UCTO_ES 105 dokladů / 336 položek,
  406 bankovních výpisů, 175 pokladních, 4 327 úhrad.

## GOTCHY (ověřené v datech, ne odhadem)

### 1. TabDokladyZbozi.CisloOrg míří na TabCisOrg.CisloOrg, NE na TabCisOrg.ID
`TabCisOrg` má **oba** sloupce. Porovnání proti `ID` dá falešných 133 chybějících organizací;
proti `CisloOrg` jich chybí 9. Totéž platí pro `Prijemce`, `MistoUrceni`, `Organizace2`.
Vždy si vytáhni FK ze `sys.foreign_keys`, nehádej.

### 2. Účetní období: ES doklady potřebují remap 40 → 1008
`UCTO_EC`: 2025=39, 2026=40 (shodné s office). `UCTO_ES`: 2025=1007, **2026=1008**.
ES doklady žijí v DB_EC a nesou `Obdobi = 40`, které v UCTO_ES **neexistuje**.
→ při přenosu ES řad přemapovat `Obdobi 40 → 1008`. Týká se i `TabBankVypisH.IdObdobi`.
Jediná výjimka z čistého 1:1.

### 3. CisloOrg 0/1 = vlastní/sesterská firma, v každé DB obráceně
`UCTO_EC`: 0 = EUROSOFT-Control (27960862), 1 = EUROSOFT-System (26411741).
`UCTO_ES`: 0 = EUROSOFT-System, 1 = EUROSOFT-Control.
14 ES dokladů (7× řada 501, 7× 601) má `CisloOrg = 0` → **remap 0 → 1**, jinak by měly
jako protistranu samy sebe. Zbytek číslování organizací je **sdílený** mezi DB_EC a DB_IS
(27 z 28 firem sedí na jméno i IČO) — riziko záměny firem nehrozí.

### 4. Položky dokladů visí na skladové vrstvě, která v cíli není
`FK__TabPohybyZbozi__IDZboSklad → TabStavSkladu` v obou cílech **existuje, je aktivní a trusted**.
`TabStavSkladu` i `TabKmenZbozi` mají v cíli 0 řádků. `IDZboSklad` je `NOT NULL` a vyplněný
u **100 % položek** (25 268/25 268) — i u účetních dokladů, nejen skladových.
→ Bez skladové vrstvy položky přenést NELZE. Vypnout FK při loadu nestačí: Helios při upgradu
FK znovu zakládá a padá na dangling (přesně to popisuje `doc-ucetnictvi-cloud-helios-xfer`).
Rozhodnutí Kristý: přenést **jen potřebné karty** — 3 271 `TabKmenZbozi` + 3 272 `TabStavSkladu`
(z celkových 17 717 / 17 682).

### 5. Řetězec pod kartami je mělký
Povinné (NOT NULL) vazby karet jen tři: `SkupZbo`→`TabSkupinyZbozi`,
`IDKmenZbozi`→`TabKmenZbozi`, `IDSklad`→`TabStrom`. Ostatní smí být NULL.
Chybí v obou cílech shodně: `TabMJ` bal/hod/m/Role (ks už tam je), `TabSkupinyZbozi`
111/500/600/610/620 (všech 5), `TabSortiment` 1/2/20. `TabSkupUKod` a `TabDPH` sedí.

### 6. Struktury tabulek sedí přesně — mapování sloupců netřeba
Porovnáno sloupec po sloupci (název, typ, délka): `TabDokladyZbozi` 334, `TabPohybyZbozi` 289,
`TabPokladna` 246, `TabBankVypisR` 138, `TabDokumenty` 138, `TabUhrady` 95, `TabBankVypisH` 64,
`TabDokumVazba` 15. Nulový rozdíl proti `UCTO_EC` i `UCTO_ES`.

### 7. Bankovní výpisy se dělí podle TabBankSpojeni.IDOrg, ne podle čísla účtu
Předloha měla natvrdo `CisloUctu='3047813002' and IDOrg=2071`. Za 2026:
Control (IDOrg 1) = účty 9251651001 (307 výpisů), 1387942581 (10), 9251651044 (8) → `UCTO_EC`;
System (IDOrg 2071) = účet 3047813002 (81 výpisů) → `UCTO_ES`. Celkem 406.

### 8. Sebereference jsou čisté
V celé přenášené množině je jediný doklad s vyplněným `StornoDoklad` a ukazuje dovnitř množiny.
`NavaznyDoklad`, `NavaznyDobropis`, `Nabidka`, `IDstin` nevyplněné nikde. Žádné visící odkazy.

### 9. Most db=mssql vrací „internal_error" i na obyčejnou chybu v SQL
Neexistující sloupec (`TabBankSpojeni.KodBanky`, `TabStavSkladu.IDZbozi`) nevrátí hlášku
SQL Serveru, ale holé `internal_error`. Nehledej problém v délce dotazu — ověř názvy sloupců
přes `INFORMATION_SCHEMA.COLUMNS`. Větev `db=pg` naproti tomu chybu vrací normálně.

### 10. Kolace: cross-db UNION na 188.12 potřebuje COLLATE DATABASE_DEFAULT
`UCTO_EC`/`UCTO_ES` = `Czech_CI_AS`, řídící `MOST` = `SQL_Czech_CP1250_CI_AS`.
UNION přes databáze bez `COLLATE DATABASE_DEFAULT` padá na „Cannot resolve collation conflict".

## Předloha
`EC_ES_PrenesDokladyDoHelios003` v DB_EC (autorka Kristýna Kšírová, 18.1.2024) + 17 dalších
procedur `EC_ES_*`. Přenáší doklady DB_EC → DB_IS **na jedné instanci** (tříčlenné názvy
`[DB_IS].[dbo].`), idempotence přes `_EXT` tabulky (`_ID_EC`). Na 188.12 **není linked server**,
takže portovat ji 1:1 nejde — proto most. Dopočty, které volá (`hp_ObehZbozi_PrepocetPolozek`,
`hp_ObehZbozi_NapocitejSumaciCen`, `EC_ES_PrijemZbozi_PrepocitejDoklad`), se musí na cíli
spustit zvlášť; poslední z nich tam vůbec neexistuje.

## Další prázdné tabulky v cíli
`TabPrikazH`, `TabPrikazR` (platební příkazy — poslední krok předlohy tedy v 1. kole vypadává),
`TabPokladnaR`, `TabUhradyR`, všechny `*_EXT`. Cíl je SQL 2025 **Express** (limit 10 GB/DB);
`UCTO_EC` 712 MB dat, `UCTO_ES` 520 MB — místa dost.

