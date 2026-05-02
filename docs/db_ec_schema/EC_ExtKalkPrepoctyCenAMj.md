# EC_ExtKalkPrepoctyCenAMj

**Schema**: dbo · **Cluster**: Other · **Rows**: 30 · **Size**: 0.02 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | ANO |  |  |
| 3 | `RegCis` | nvarchar(30) | NE |  |  |
| 4 | `Dodavatel` | int | ANO |  |  |
| 5 | `Nazev` | nvarchar(160) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(160) | ANO |  |  |
| 7 | `PC_Koef` | smallint | NE |  |  |
| 8 | `PC_MJ` | nvarchar(10) | ANO |  |  |
| 9 | `NC_Koef` | smallint | NE |  |  |
| 10 | `NC_MJ` | nvarchar(10) | ANO |  |  |
| 11 | `JC_Koef` | smallint | NE |  |  |
| 12 | `JC_MJ` | nvarchar(10) | ANO |  |  |
| 13 | `KC_Koef` | smallint | NE |  |  |
| 14 | `KC_MJ` | nvarchar(10) | ANO |  |  |
| 15 | `Blokovano` | bit | NE |  |  |
| 16 | `Autor` | nvarchar(128) | NE |  |  |
| 17 | `DatPorizeni` | datetime | NE |  |  |
| 18 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 19 | `DatZmeny` | datetime | ANO |  |  |
| 20 | `IndArchiv` | int | NE |  |  |
