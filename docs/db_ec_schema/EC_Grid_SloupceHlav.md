# EC_Grid_SloupceHlav

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,394 · **Size**: 0.97 MB · **Sloupců**: 26 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `GridName` | nvarchar(100) | ANO |  |  |
| 3 | `FormName` | nvarchar(100) | ANO |  |  |
| 4 | `CisloPrehledu` | int | ANO |  |  |
| 5 | `GridGUID` | uniqueidentifier | ANO |  |  |
| 6 | `ViewGUID` | uniqueidentifier | ANO |  |  |
| 7 | `Nazev` | nvarchar(100) | ANO |  |  |
| 8 | `Popis` | nvarchar(100) | ANO |  |  |
| 9 | `AppName` | nvarchar(50) | ANO |  |  |
| 10 | `AppExeName` | nvarchar(100) | ANO |  |  |
| 11 | `AppTitle` | nvarchar(50) | ANO |  |  |
| 12 | `Login` | nvarchar(50) | ANO |  |  |
| 13 | `Datum` | datetime | NE | (getdate()) |  |
| 14 | `FormHeight` | smallint | ANO |  |  |
| 15 | `FormWidth` | smallint | ANO |  |  |
| 16 | `Def` | bit | ANO |  |  |
| 17 | `CisloZam` | int | ANO |  |  |
| 18 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 19 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 20 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 21 | `DatZmeny` | datetime | ANO |  |  |
| 22 | `SortString` | nvarchar(50) | ANO |  |  |
| 23 | `PoslPouziti` | nvarchar(128) | ANO |  |  |
| 24 | `DatPoslPouziti` | datetime | ANO |  |  |
| 25 | `FontSize` | int | ANO | ((8)) |  |
| 26 | `ZobrazujFiltr` | bit | ANO | ((1)) |  |

## Indexy

- **PK** `PK_EC_Grid_SloupceHlav` (CLUSTERED) — `ID`
