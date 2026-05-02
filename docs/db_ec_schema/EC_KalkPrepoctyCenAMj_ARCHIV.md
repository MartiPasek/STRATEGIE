# EC_KalkPrepoctyCenAMj_ARCHIV

**Schema**: dbo · **Cluster**: Production · **Rows**: 95 · **Size**: 0.02 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloVerze` | int | NE |  |  |
| 3 | `Platnost` | bit | NE |  |  |
| 4 | `IDKmenZbozi` | int | ANO |  |  |
| 5 | `RegCis` | nvarchar(30) | NE |  |  |
| 6 | `Dodavatel` | int | ANO |  |  |
| 7 | `Nazev` | nvarchar(160) | ANO |  |  |
| 8 | `Poznamka` | nvarchar(160) | ANO |  |  |
| 9 | `PC_Koef` | smallint | NE |  |  |
| 10 | `PC_MJ` | nvarchar(10) | ANO |  |  |
| 11 | `NC_Koef` | smallint | NE |  |  |
| 12 | `NC_MJ` | nvarchar(10) | ANO |  |  |
| 13 | `JC_Koef` | smallint | NE |  |  |
| 14 | `JC_MJ` | nvarchar(10) | ANO |  |  |
| 15 | `KC_Koef` | smallint | NE |  |  |
| 16 | `KC_MJ` | nvarchar(10) | ANO |  |  |
| 17 | `Blokovano` | bit | NE |  |  |
| 18 | `Autor` | nvarchar(128) | NE |  |  |
| 19 | `DatPorizeni` | datetime | NE |  |  |
| 20 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 21 | `DatZmeny` | datetime | ANO |  |  |
