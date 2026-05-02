# EC_GrafSestavy

**Schema**: dbo · **Cluster**: Other · **Rows**: 17 · **Size**: 0.07 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | tinyint | ANO |  |  |
| 3 | `Typtext` | varchar(14) | NE |  |  |
| 4 | `ID_Rastru` | int | ANO |  |  |
| 5 | `Prehled` | int | ANO |  |  |
| 6 | `RastrS` | tinyint | ANO |  |  |
| 7 | `RastrR` | tinyint | ANO |  |  |
| 8 | `RastrS_end` | tinyint | ANO |  |  |
| 9 | `RastrR_end` | tinyint | ANO |  |  |
| 10 | `Poradi` | int | ANO |  |  |
| 11 | `IDGrafu` | int | ANO |  |  |
| 12 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_GrafySestavy` (CLUSTERED) — `ID`
