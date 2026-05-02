# EC_Grid_UzivatelskaNastaveni

**Schema**: dbo · **Cluster**: Other · **Rows**: 550 · **Size**: 0.13 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDSestavy` | int | NE |  |  |
| 3 | `CisloZam` | int | NE |  |  |
| 4 | `IndVychozi` | bit | NE | ((0)) |  |
| 5 | `IndOblibene` | bit | NE | ((0)) |  |
| 6 | `_DTStamp` | datetime | NE | (getdate()) |  |
| 7 | `_UserID` | nvarchar(128) | NE | (suser_name()) |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Grid_UzivatelskaNastaveni` (CLUSTERED) — `IDSestavy, CisloZam`
