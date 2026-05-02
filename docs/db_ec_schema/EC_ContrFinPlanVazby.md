# EC_ContrFinPlanVazby

**Schema**: dbo · **Cluster**: Other · **Rows**: 41,701 · **Size**: 4.00 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDFaPol` | int | ANO |  |  |
| 3 | `IDFaktury` | int | ANO |  |  |
| 4 | `IDObjPol` | int | ANO |  |  |
| 5 | `IDObj` | int | ANO |  |  |
| 6 | `IDFinPlan` | int | ANO |  |  |
| 7 | `IDPredpis` | int | ANO |  |  |
| 8 | `IDPokl` | int | ANO |  |  |
| 9 | `IDPolPokl` | int | ANO |  |  |
| 10 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ContrFinPlanVazby` (CLUSTERED) — `ID`
