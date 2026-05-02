# EC_CenikyTxtVzorcePar

**Schema**: dbo · **Cluster**: Finance · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `IDCenik` | int | ANO |  |  |
| 2 | `P01` | nvarchar(15) | ANO |  |  |
| 3 | `P02` | nvarchar(15) | ANO |  |  |
| 4 | `P03` | nvarchar(15) | ANO |  |  |
| 5 | `P04` | nvarchar(15) | ANO |  |  |
| 6 | `P05` | nvarchar(15) | ANO |  |  |
| 7 | `P06` | nvarchar(15) | ANO |  |  |
| 8 | `P07` | nvarchar(15) | ANO |  |  |
| 9 | `P08` | nvarchar(15) | ANO |  |  |
| 10 | `P09` | nvarchar(15) | ANO |  |  |
| 11 | `P10` | nvarchar(15) | ANO |  |  |
| 12 | `P11` | nvarchar(15) | ANO |  |  |
| 13 | `P12` | nvarchar(15) | ANO |  |  |
| 14 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |
| 18 | `Zmenil` | nvarchar(128) | ANO |  |  |
