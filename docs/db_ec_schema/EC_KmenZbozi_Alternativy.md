# EC_KmenZbozi_Alternativy

**Schema**: dbo · **Cluster**: Production · **Rows**: 7 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `RegCisZdroj` | nvarchar(60) | ANO |  |  |
| 3 | `RegCisCil` | nvarchar(60) | ANO |  |  |
| 4 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `Poznamka` | nvarchar(1000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_KmenZbozi_Alternativy` (CLUSTERED) — `ID`
