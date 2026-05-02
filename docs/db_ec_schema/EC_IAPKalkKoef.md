# EC_IAPKalkKoef

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.01 MB · **Sloupců**: 19 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID2` | int | ANO |  |  |
| 2 | `ID2Koef` | int | ANO |  |  |
| 3 | `ID` | int | NE |  |  |
| 4 | `IDKmenZbozi` | int | ANO |  |  |
| 5 | `K_ARB` | numeric(5,2) | ANO |  |  |
| 6 | `K_VKM` | numeric(5,2) | ANO |  |  |
| 7 | `Puvod` | nvarchar(100) | ANO |  |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `K_ARB_Neshoda` | numeric(5,2) | ANO |  |  |
| 10 | `K_VKM_Neshoda` | numeric(5,2) | ANO |  |  |
| 11 | `Puvod_Neshoda` | nvarchar(100) | ANO |  |  |
| 12 | `Blokovano` | bit | NE |  |  |
| 13 | `Zamceno` | bit | NE |  |  |
| 14 | `DatZamceni` | datetime | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | NE |  |  |
| 16 | `DatPorizeni` | datetime | NE |  |  |
| 17 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 18 | `DatZmeny` | datetime | ANO |  |  |
| 19 | `IndArchiv` | int | NE |  |  |
