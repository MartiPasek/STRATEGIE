# EC_DELPHI_TabOffline

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 33 · **Size**: 0.20 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | NE |  |  |
| 3 | `Nazev` | nvarchar(50) | NE |  |  |
| 4 | `Popis` | ntext | ANO |  |  |
| 5 | `OnlineSelect` | ntext | ANO |  |  |
| 6 | `OfflineTable` | nvarchar(50) | ANO |  |  |
| 7 | `OfflineTableCols` | ntext | ANO |  |  |
| 8 | `ModeNr` | int | ANO |  |  |
| 9 | `Aktivni` | bit | NE | ((0)) |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `ZmenilData` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmenyDat` | datetime | ANO |  |  |
| 17 | `SynchronizacniSelect` | ntext | ANO |  |  |
| 18 | `Synchronizuj` | bit | ANO |  |  |
| 19 | `IntervalSynchronizace` | int | ANO |  |  |
| 20 | `SelectPocetZaznamu` | ntext | ANO |  |  |
| 21 | `CasPoslSync` | datetime2 | ANO |  |  |

## Indexy

- **PK** `PK_EC_DELPHI_TabOffline` (CLUSTERED) — `ID`
