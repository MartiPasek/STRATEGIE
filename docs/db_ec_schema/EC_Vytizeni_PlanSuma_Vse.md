# EC_Vytizeni_PlanSuma_Vse

**Schema**: dbo · **Cluster**: Production · **Rows**: 6,245 · **Size**: 1.63 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 3 | `Datum` | date | ANO |  |  |
| 4 | `PocetHodin` | int | ANO |  |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(126) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 10 | `Typ` | int | ANO |  |  |
| 11 | `Blokovano` | bit | ANO |  |  |
| 12 | `Barva` | nvarchar(10) | ANO |  |  |
| 13 | `BarvaRamecek` | nvarchar(10) | ANO |  |  |
| 14 | `ZobrazujNuly` | bit | ANO | ((0)) |  |
| 15 | `JsemInstalace` | bit | ANO | ((0)) |  |
| 16 | `Externe` | bit | ANO | ((0)) |  |
| 17 | `BarvaPisma` | nvarchar(10) | ANO | ('000000') |  |
| 18 | `PoznamkaUziv` | nvarchar(4000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_PlanSuma_Vse` (CLUSTERED) — `ID`
