# EC_ContrKontroly

**Schema**: dbo · **Cluster**: Other · **Rows**: 9,284 · **Size**: 1.74 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | int | NE | ((0)) |  |
| 3 | `Text` | nvarchar(250) | ANO |  |  |
| 4 | `Castka` | numeric(18,2) | ANO |  |  |
| 5 | `Procedura` | nvarchar(100) | ANO |  |  |
| 6 | `OK` | bit | NE | ((0)) |  |
| 7 | `Error` | bit | NE | ((0)) |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatZmeny` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ContrKontroly` (CLUSTERED) — `ID`
