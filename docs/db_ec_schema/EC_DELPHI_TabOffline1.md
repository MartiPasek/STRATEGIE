# EC_DELPHI_TabOffline1

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 7 · **Size**: 0.09 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `AppNr` | int | NE |  |  |
| 3 | `Cislo` | int | NE |  |  |
| 4 | `Nazev` | nvarchar(50) | NE |  |  |
| 5 | `Popis` | ntext | ANO |  |  |
| 6 | `OnlineSelect` | ntext | ANO |  |  |
| 7 | `OfflineTable` | nvarchar(50) | ANO |  |  |
| 8 | `OfflineTableCols` | ntext | ANO |  |  |
| 9 | `ModeNr` | int | ANO |  |  |
| 10 | `Aktivni` | bit | NE | ((0)) |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |
| 15 | `ZmenilData` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmenyDat` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_DELPHI_TabOffline1` (CLUSTERED) — `ID`
