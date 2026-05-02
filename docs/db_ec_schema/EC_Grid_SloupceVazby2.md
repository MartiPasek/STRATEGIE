# EC_Grid_SloupceVazby2

**Schema**: dbo · **Cluster**: Other · **Rows**: 161 · **Size**: 0.02 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDSloupce` | int | NE |  |  |
| 3 | `IDPodminky` | int | NE |  |  |
| 4 | `Autor` | nvarchar(128) | NE |  |  |
| 5 | `DatPorizeni` | datetime | NE |  |  |
| 6 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |
| 8 | `DatPorizeni_D` | int | ANO |  |  |
| 9 | `DatPorizeni_M` | int | ANO |  |  |
| 10 | `DatPorizeni_Y` | int | ANO |  |  |
| 11 | `DatPorizeni_Q` | int | ANO |  |  |
| 12 | `DatPorizeni_W` | int | ANO |  |  |
| 13 | `DatPorizeni_X` | datetime | ANO |  |  |
| 14 | `Poradi` | tinyint | ANO |  |  |
| 15 | `IndRowSelect` | bit | NE |  |  |
