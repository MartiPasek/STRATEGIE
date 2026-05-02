# EC_KmenZbozi_NahradyRegCis

**Schema**: dbo · **Cluster**: Production · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `RegCisHeo` | nvarchar(100) | ANO |  |  |
| 3 | `RegCisCil` | nvarchar(100) | ANO |  |  |
| 4 | `CisloOrgCil` | int | ANO |  |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Poznamka` | nvarchar(1000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_KmenZbozi_NahradyRegCis` (CLUSTERED) — `ID`
