# EC_KontrolaCeny

**Schema**: dbo · **Cluster**: Other · **Rows**: 9,647 · **Size**: 1.52 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKalkPol` | int | NE |  |  |
| 3 | `IDCenikPol` | int | ANO |  |  |
| 4 | `RegCis` | nvarchar(30) | ANO |  |  |
| 5 | `CenikNC` | numeric(18,2) | ANO |  |  |
| 6 | `EinheitPreis` | numeric(18,2) | ANO |  |  |
| 7 | `CenikMena` | nvarchar(3) | ANO | (N'EUR') |  |
| 8 | `Poznamka` | nvarchar(500) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_KontrolaCeny` (CLUSTERED) — `ID`
