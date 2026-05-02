# EC_KalkKoeficientyZalohaNesahat

**Schema**: dbo · **Cluster**: Production · **Rows**: 4,037 · **Size**: 0.70 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 0

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
| 13 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 14 | `Autor` | nvarchar(128) | NE |  |  |
| 15 | `DatPorizeni` | datetime | NE |  |  |
| 16 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |
| 18 | `IndArchiv` | int | NE |  |  |
