# EC_FormDef

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 910 · **Size**: 0.99 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE | ([dbo].[EC_Get_NEWID_2]('EC_FormDef')) |  |
| 2 | `Nazev` | nvarchar(150) | ANO |  |  |
| 3 | `IDNadrazene` | int | ANO |  |  |
| 4 | `SQL_Select` | ntext | ANO |  |  |
| 5 | `ParentName` | nvarchar(50) | ANO |  |  |
| 6 | `fTop` | int | NE | ((200)) |  |
| 7 | `fLeft` | int | NE | ((300)) |  |
| 8 | `fHeight` | int | NE | ((500)) |  |
| 9 | `fWidth` | int | NE | ((600)) |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `EditModeCondition` | nvarchar(2000) | NE | ('') |  |
| 15 | `FMX` | tinyint | ANO | ((1)) | 1 = VLC, 2 = FMX |
| 16 | `FocusKomponent` | nvarchar(10) | ANO |  |  |
| 17 | `Sys` | bit | NE | ((0)) |  |

## Indexy

- **PK** `PK_EC_FormDef` (CLUSTERED) — `ID`
