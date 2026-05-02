# EC_ExtKalkKoeficienty

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,605 · **Size**: 0.51 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | ANO |  |  |
| 3 | `K_ARB` | numeric(5,2) | ANO |  |  |
| 4 | `K_VKM` | numeric(5,2) | ANO |  |  |
| 5 | `Puvod` | nvarchar(100) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 7 | `K_ARB_Neshoda` | numeric(5,2) | ANO |  |  |
| 8 | `K_VKM_Neshoda` | numeric(5,2) | ANO |  |  |
| 9 | `Puvod_Neshoda` | nvarchar(100) | ANO |  |  |
| 10 | `Blokovano` | bit | NE |  |  |
| 11 | `Zamceno` | bit | NE |  |  |
| 12 | `DatZamceni` | datetime | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE |  |  |
| 14 | `DatPorizeni` | datetime | NE |  |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |
| 17 | `IndArchiv` | int | NE |  |  |
| 18 | `Zamknul` | nvarchar(128) | ANO |  |  |
