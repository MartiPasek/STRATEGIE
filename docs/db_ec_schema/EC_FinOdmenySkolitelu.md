# EC_FinOdmenySkolitelu

**Schema**: dbo · **Cluster**: Finance · **Rows**: 234 · **Size**: 0.13 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloN` | int | ANO |  |  |
| 3 | `CisloS` | int | ANO |  |  |
| 4 | `Typ` | int | ANO |  |  |
| 5 | `DatNastupu` | datetime | ANO |  |  |
| 6 | `DoVyplaty` | datetime | ANO |  |  |
| 7 | `Castka` | numeric(18,2) | ANO |  |  |
| 8 | `Vyplaceno` | bit | ANO | ((0)) |  |
| 9 | `Ukonceni` | datetime | ANO |  |  |
| 10 | `DatDoVyplaty_Y` | int | ANO |  |  |
| 11 | `Poznamka` | nvarchar(250) | ANO |  |  |
| 12 | `DruhSmlouvy` | int | ANO | ((0)) |  |
| 13 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 16 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_FinOdmenySkolitelu` (CLUSTERED) — `ID`
