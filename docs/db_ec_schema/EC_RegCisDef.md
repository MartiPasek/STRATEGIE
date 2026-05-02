# EC_RegCisDef

**Schema**: dbo · **Cluster**: Other · **Rows**: 60 · **Size**: 0.07 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

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
| 11 | `PouzivaTakeAlternativRegCis` | bit | ANO | ((0)) |  |
| 12 | `DoplnitNulamiZlevaNa` | tinyint | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_RegCisDodavatel` (CLUSTERED) — `ID`
