# EC_GrafyaVzory

**Schema**: dbo · **Cluster**: Other · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloGrafu` | int | ANO |  |  |
| 3 | `NazevGrafu` | nvarchar(200) | ANO |  |  |
| 4 | `CisloVzoru` | int | ANO |  |  |
| 5 | `NazevVzoru` | nvarchar(200) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 7 | `Vzor` | bit | NE | ((0)) |  |
| 8 | `Graf` | bit | NE | ((0)) |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_GrafyVzory` (CLUSTERED) — `ID`
