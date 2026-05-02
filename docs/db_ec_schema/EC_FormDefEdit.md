# EC_FormDefEdit

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 9,887 · **Size**: 1.68 MB · **Sloupců**: 24 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE | ([dbo].[EC_GET_NewID_2]('EC_FormDefEdit')) |  |
| 2 | `ID_Form` | int | ANO |  |  |
| 3 | `ID_Prehled` | int | ANO |  |  |
| 4 | `User` | nvarchar(50) | ANO |  |  |
| 5 | `Typ` | int | NE | ((2)) |  |
| 6 | `cTop` | int | NE | ((60)) |  |
| 7 | `cLeft` | int | NE | ((60)) |  |
| 8 | `cHeight` | int | NE | ((20)) |  |
| 9 | `cWidth` | int | NE | ((100)) |  |
| 10 | `cFieldName` | nvarchar(50) | NE | ('') |  |
| 11 | `cFieldDataTyp` | int | ANO |  |  |
| 12 | `cParent` | nvarchar(50) | ANO | ('') |  |
| 13 | `cCaption` | nvarchar(50) | NE | ('') |  |
| 14 | `cMask` | nvarchar(100) | NE | ('') |  |
| 15 | `cDirectory` | nvarchar(250) | NE | ('') |  |
| 16 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 17 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 18 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 19 | `DatZmeny` | datetime | ANO |  |  |
| 20 | `Smazal` | nvarchar(128) | ANO |  |  |
| 21 | `Smazana` | bit | NE | ((0)) |  |
| 22 | `Prevedena` | bit | NE | ((1)) |  |
| 23 | `FMX` | tinyint | ANO | ((1)) | 1 = VLC, 2 = FMX |
| 24 | `Sys` | bit | NE | ((0)) |  |

## Cizí klíče (declared)

- `ID_Form` → [`EC_FormDef`](EC_FormDef.md).`ID` _(constraint: `FK_EC_FormDefEdit_EC_FormDef`)_

## Indexy

- **PK** `PK_EC_FormDefEdit` (CLUSTERED) — `ID`
