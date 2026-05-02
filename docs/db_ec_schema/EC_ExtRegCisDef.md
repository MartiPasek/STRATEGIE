# EC_ExtRegCisDef

**Schema**: dbo · **Cluster**: Other · **Rows**: 60 · **Size**: 0.02 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Pos` | smallint | ANO |  |  |
| 3 | `Vyrobce` | nvarchar(30) | NE |  |  |
| 4 | `RegCisZkratka` | nvarchar(8) | NE |  |  |
| 5 | `ObsahujeText` | nvarchar(30) | ANO |  |  |
| 6 | `PrikladRegCisVyrobce` | nvarchar(30) | ANO |  |  |
| 7 | `PrikladRegCisHelios` | nvarchar(30) | ANO |  |  |
| 8 | `VsechnaVelkaPismena` | bit | ANO |  |  |
| 9 | `ZadneMezery` | bit | ANO |  |  |
| 10 | `NahraditOza0` | bit | ANO |  |  |
| 11 | `PouzivaTakeAlternativRegCis` | bit | ANO |  |  |
| 12 | `DoplnitNulamiZlevaNa` | tinyint | ANO |  |  |
| 13 | `DatPorizeni` | datetime | NE |  |  |
| 14 | `Autor` | nvarchar(128) | NE |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
| 16 | `Zmenil` | nvarchar(128) | ANO |  |  |
