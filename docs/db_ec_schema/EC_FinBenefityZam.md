# EC_FinBenefityZam

**Schema**: dbo · **Cluster**: Finance · **Rows**: 11 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Benefit` | nvarchar(250) | ANO |  |  |
| 3 | `Hodnota` | numeric(18,0) | ANO |  |  |
| 4 | `Podminka` | nvarchar(250) | ANO |  |  |
| 5 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_FinBenefityZam` (CLUSTERED) — `ID`
