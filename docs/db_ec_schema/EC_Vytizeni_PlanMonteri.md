# EC_Vytizeni_PlanMonteri

**Schema**: dbo · **Cluster**: Production · **Rows**: 11,107 · **Size**: 4.02 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 4 | `Datum` | date | ANO |  |  |
| 5 | `PocetHodin` | int | ANO |  |  |
| 6 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(126) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 11 | `Typ` | int | ANO |  |  |
| 12 | `CisloZam` | int | ANO |  |  |
| 13 | `JsemMonter` | bit | ANO | ((1)) |  |

## Indexy

- **PK** `PK_EC_Vytizeni_PlanMonteri` (CLUSTERED) — `ID`
