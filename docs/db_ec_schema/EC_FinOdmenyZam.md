# EC_FinOdmenyZam

**Schema**: dbo · **Cluster**: Finance · **Rows**: 65 · **Size**: 0.13 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Doporucen` | nvarchar(50) | ANO |  |  |
| 4 | `TerminPohovoru` | datetime | ANO |  |  |
| 5 | `Castka` | numeric(9,2) | ANO |  |  |
| 6 | `Typ` | int | ANO |  |  |
| 7 | `DruhOdmeny` | nvarchar(MAX) | ANO |  |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `PracSmlouvaOd` | datetime | ANO |  |  |
| 10 | `Vyplaceno` | bit | ANO | ((0)) |  |
| 11 | `DoVyplaty` | datetime | ANO |  |  |
| 12 | `DruhSmlouvy` | int | ANO | ((0)) |  |
| 13 | `DatDoVyplaty_Y` | int | ANO |  |  |
| 14 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 15 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 16 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 17 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_FinOdmenyZam` (CLUSTERED) — `ID`
