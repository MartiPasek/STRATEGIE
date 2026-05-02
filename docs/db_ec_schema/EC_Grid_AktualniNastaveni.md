# EC_Grid_AktualniNastaveni

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `FormName` | nvarchar(100) | NE |  |  |
| 4 | `GridName` | nvarchar(100) | NE |  |  |
| 5 | `CisloPrehledu` | int | NE |  |  |
| 6 | `IDSestavy` | int | NE |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Grid_AktualniNastaveni` (CLUSTERED) — `CisloZam, FormName, GridName, CisloPrehledu`
