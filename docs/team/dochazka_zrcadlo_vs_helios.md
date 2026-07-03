# Docházka: jak porovnat NAŠE ZRCADLO s HELIOSEM (Centrála) — návod

> Pro Claude-26 (Peťa) i ostatní instance. Autor: Claude-23 / ID23, 3. 7. 2026.
> Vzniklo z reálné kontroly „4 lidi" (Svatoš/Bláha/Jirkovský/Trunec) od Petry.

## Co je co (drž tohle, jinak v tom plaveš)

- **NAŠE ZRCADLO** = `tenant.att_day_summary` (PG, `db=pg`). Sloupec **`cas_celkem`** = odpracováno/den. Je to **snímek** Centrály k okamžiku posledního zrcadlení — může zaostávat!
- **HELIOS denní souhrn** = `EC_Dochazka_SumaDen` (DB_EC, `db=mssql`). Sloupec **`CasCelkem`**. **Toto je přesně „Helios podklad" k výplatám** (ověřeno na setiny). Zdroj pravdy.
- **HELIOS detail (píchnutí)** = `EC_Dochazka` (DB_EC, `db=mssql`). Jednotlivé záznamy s **`Autor`**, `CasZacatek`/`CasKonec`, `DruhCinnosti`.
  - `Autor='DochazkaTablet'` = reálné píchnutí na tabletu.
  - `Autor=<login, např. LTrunec>` = **ruční** zadání zaměstnancem/vedoucím.
  - `Autor='STRATEGIE'` = naše propsané (dopíchnutí). *(Do Centrály ale běžně NEZAPISUJEME — viz doktrína.)*
- **DruhCinnosti** (v EC_Dochazka): `4` = práce (tablet), **`20` = dovolená**, `116` = práce (jiné středisko)… Pozor: **dovolená (20) je v `CasCelkem` jako 8 h**, ale NENÍ to odpracováno! (Číselník `TabDruhCinnosti` je jen CRM Dodavatel/Odberatel — docházkové kódy jsou interní, ptej se Dušana/Petry.)

## Klíč k mapování osob
`att_day_summary.cislo_zam` = EC číslo zaměstnance (435, 465, …). V EC je to `EC_Dochazka.CisloZam` / `EC_Dochazka_SumaDen.CisloZam`. **`DatumPripadu` v EC je datetime** → filtruj rozsahem (`>= '2026-06-01' AND < '2026-07-01'`), ne `IN ('2026-06-30')`.

## Postup ve 3 krocích (bridge: CLAUDE_SQL.sql přes Write tool + CLAUDE_GO.txt)

### 1) Měsíční součet obou stran → kde je rozdíl
NAŠE (`db=pg`):
```sql
SELECT cislo_zam, ROUND(SUM(cas_celkem)::numeric,2) nase
FROM tenant.att_day_summary
WHERE tenant_id=2 AND rok=2026 AND mesic=6 AND cislo_zam IN (435,465,476,486)
GROUP BY cislo_zam ORDER BY cislo_zam;
```
HELIOS (`db=mssql`):
```sql
SELECT CisloZam, SUM(CasCelkem) helios
FROM EC_Dochazka_SumaDen
WHERE DatumPripadu_Y=2026 AND DatumPripadu_M=6 AND CisloZam IN (435,465,476,486)
GROUP BY CisloZam ORDER BY CisloZam;
```
Helios = pravda. Rozdíl `nase - helios` ukáže, u koho to nesedí.

### 2) U koho nesedí → jdi po dnech (najdi konkrétní den)
Stejné dotazy, ale `datum`/`DatumPripadu` po dnech pro toho jednoho člověka. Dny 1:1 porovnej — najdeš den, kde se liší (často **poslední dny měsíce**, které Centrála doplnila až po našem zrcadlení).

### 3) Sporný den → otevři HELIOS detail (`db=mssql`)
```sql
SELECT Autor, CONVERT(varchar(19),CasZacatek,120) zac, CONVERT(varchar(19),CasKonec,120) kon,
       CasCelkemVcRezii celkem, DruhCinnosti dc, CAST(Poznamka AS varchar(80)) pozn
FROM EC_Dochazka
WHERE CisloZam=465 AND DatumPripadu >= '2026-06-30' AND DatumPripadu < '2026-07-01'
ORDER BY CasZacatek;
```
Podle `Autor` + `DruhCinnosti` poznáš, jestli je den reálný (tablet, práce), ruční (login), nebo dovolená (dc=20).

## Časté příčiny rozdílu + co s tím
1. **Náš snímek zaostává** (Centrála doplněna po zrcadlení) → nejčastější. **Srovnání:** `@@DOCHSUM <rok> <mesic>` = přezrcadlí měsíc 1:1 z `EC_Dochazka_SumaDen` (bez banneru). Tím se naše zrcadlo srovná na Helios.
2. **Ruční sebe-záznam** (`Autor`=login, kulatých 8:00–16:00) → ověřit u Dušana/Petry, jestli je legitimní.
3. **Dovolená (dc=20)** vede v `CasCelkem` jako 8 h — je v součtu, ale je to dovolená, ne práce. Při posuzování „odpracováno" to odděl.

## DOKTRÍNA (nepřekroč)
- **Do Centrály (EC_Dochazka) NEZAPISUJEME.** Když jsou data v Centrále špatně, opraví je **Dušan v Centrále**, my pak jen **přezrcadlíme** (`@@DOCHSUM`). Náš směr je Helios → naše zrcadlo, ne obráceně.
- Červen bývá ve fázi výplat — přezrcadlení měsíce dělej **po odsouhlasení** Petrou/Marti, ne naslepo.
