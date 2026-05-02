# EC_Hala_PLCLog_CheckList

**Schema**: dbo · **Cluster**: Production · **Rows**: 15 · **Size**: 0.07 MB · **Sloupců**: 27 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Popis` | nvarchar(200) | ANO |  |  |
| 3 | `Area` | int | ANO |  |  |
| 4 | `Area_text` | varchar(14) | NE |  |  |
| 5 | `DBNum` | int | ANO | ((0)) |  |
| 6 | `Start` | int | ANO | ((0)) |  |
| 7 | `Amount` | int | ANO | ((0)) |  |
| 8 | `WLen` | int | ANO |  |  |
| 9 | `WLen_text` | varchar(7) | NE |  |  |
| 10 | `Async` | bit | NE | ((0)) |  |
| 11 | `Adresa` | nvarchar(25) | ANO |  |  |
| 12 | `_Popis` | nvarchar(200) | ANO |  |  |
| 13 | `_Area` | int | ANO |  |  |
| 14 | `_Area_text` | varchar(14) | NE |  |  |
| 15 | `_DBNum` | int | ANO | ((0)) |  |
| 16 | `_Start` | int | ANO | ((0)) |  |
| 17 | `_Amount` | int | ANO | ((0)) |  |
| 18 | `_WLen` | int | ANO |  |  |
| 19 | `_WLen_text` | varchar(7) | NE |  |  |
| 20 | `_Async` | bit | ANO | ((0)) |  |
| 21 | `_Adresa` | nvarchar(25) | ANO |  |  |
| 22 | `Timer_s` | int | NE | ((1)) |  |
| 23 | `Enable` | bit | NE | ((0)) |  |
| 24 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 25 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 26 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 27 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Hala_PLCLog_CheckList` (CLUSTERED) — `ID`
