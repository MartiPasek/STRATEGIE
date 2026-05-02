# EC_KalkPrepoctyCenAMj

**Schema**: dbo · **Cluster**: Production · **Rows**: 33 · **Size**: 0.07 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | ANO |  |  |
| 3 | `RegCis` | nvarchar(30) | NE |  |  |
| 4 | `Dodavatel` | int | ANO |  |  |
| 5 | `Nazev` | nvarchar(160) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(160) | ANO |  |  |
| 7 | `PC_Koef` | smallint | NE | ((1)) |  |
| 8 | `PC_MJ` | nvarchar(10) | ANO |  |  |
| 9 | `NC_Koef` | smallint | NE | ((1)) |  |
| 10 | `NC_MJ` | nvarchar(10) | ANO |  |  |
| 11 | `JC_Koef` | smallint | NE | ((1)) |  |
| 12 | `JC_MJ` | nvarchar(10) | ANO |  |  |
| 13 | `KC_Koef` | smallint | NE | ((1)) |  |
| 14 | `KC_MJ` | nvarchar(10) | ANO |  |  |
| 15 | `Blokovano` | bit | NE | ((0)) |  |
| 16 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 17 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 18 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 19 | `DatZmeny` | datetime | ANO |  |  |
| 20 | `IndArchiv` | int | NE |  |  |

## Indexy

- **PK** `PK_EC_KalkPrepoctyCenAMj` (CLUSTERED) — `ID`
