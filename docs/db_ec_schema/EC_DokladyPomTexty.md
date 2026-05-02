# EC_DokladyPomTexty

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 113 · **Size**: 0.34 MB · **Sloupců**: 18 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Druh` | tinyint | ANO |  |  |
| 3 | `Popis` | varchar(18) | ANO |  |  |
| 4 | `Jazyk` | nvarchar(3) | ANO | ('CZ') |  |
| 5 | `Pohlavi` | bit | ANO | ((0)) |  |
| 6 | `CisloOrg` | int | ANO |  |  |
| 7 | `CisloKOs` | int | ANO |  |  |
| 8 | `RadaDokladu` | int | ANO |  |  |
| 9 | `CisloZam` | int | ANO |  |  |
| 10 | `Text` | ntext | ANO |  |  |
| 11 | `Text2` | ntext | ANO |  |  |
| 12 | `Text3` | ntext | ANO |  |  |
| 13 | `Email` | bit | NE | ((0)) |  |
| 14 | `Tisk` | bit | NE | ((0)) |  |
| 15 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 16 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 17 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 18 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `ID` → [`EC_DokladyPomTexty`](EC_DokladyPomTexty.md).`ID` _(constraint: `FK_EC_DokladyPomTexty_EC_DokladyPomTexty`)_

## Indexy

- **PK** `PK_EC_DokladyPomTexty` (CLUSTERED) — `ID`
