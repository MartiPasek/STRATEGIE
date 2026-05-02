# EC_TiskZdrojeDat

**Schema**: dbo · **Cluster**: Other · **Rows**: 416 · **Size**: 1.19 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(50) | ANO |  |  |
| 3 | `IDNadrazeneSkupiny` | int | ANO |  |  |
| 4 | `NazevNadrazeneSkupiny` | nvarchar(50) | ANO |  |  |
| 5 | `IDFormDef` | int | ANO |  |  |
| 7 | `SQL_Select` | ntext | ANO |  |  |
| 9 | `Poznamka` | ntext | ANO |  |  |
| 10 | `Poradi` | tinyint | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZdrojeTiskDat` (CLUSTERED) — `ID`
