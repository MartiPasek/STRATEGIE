# EC_FormDefPopupMenu

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 10,191 · **Size**: 2.42 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE | ([dbo].[EC_GET_NewID_2]('EC_FormDefPopupMenu')) |  |
| 2 | `CisloPrehledu` | int | ANO |  |  |
| 3 | `Nazev` | nvarchar(70) | ANO |  |  |
| 4 | `UserGridAction` | bit | NE | ((0)) |  |
| 5 | `NadrazenePM` | int | ANO |  |  |
| 6 | `Poradi` | int | ANO |  |  |
| 7 | `Ikona` | int | ANO |  |  |
| 8 | `KlavZkratka` | nchar(50) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |
| 13 | `Refresh` | bit | NE | ((1)) |  |
| 14 | `ShortCut` | nvarchar(50) | ANO |  |  |
| 15 | `Typ` | smallint | ANO | ((0)) | 1 = nový, 2= Oprava, 3 = Smazat, 4 = Export, 5 = Kopírovat do schránky, 6 = Vložit ze schránky, 7 = Kopie položky |
| 16 | `Dev_ViewOnly` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_FormDefPopupMenu` (CLUSTERED) — `ID`
