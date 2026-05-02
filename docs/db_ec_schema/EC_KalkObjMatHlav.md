# EC_KalkObjMatHlav

**Schema**: dbo · **Cluster**: Production · **Rows**: 7,481 · **Size**: 1.05 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKalk` | int | ANO |  |  |
| 3 | `PoradoveCislo` | int | ANO |  |  |
| 4 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `ZalozitDochazku` | bit | ANO |  |  |
| 8 | `ProdlouzenaZaruka` | bit | ANO |  |  |
| 9 | `DatumDodaniMat` | datetime | ANO |  |  |
| 10 | `DatumOdvozu` | datetime | ANO |  |  |
| 11 | `KKO` | bit | ANO |  |  |
| 12 | `DatumDodaniRittal` | datetime | ANO |  |  |
| 13 | `Poradi` | int | ANO |  |  |
| 14 | `Beistelung` | varbinary(MAX) | ANO |  |  |
