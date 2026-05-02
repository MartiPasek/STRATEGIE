# EC_SvetlaVazbySkupiny

**Schema**: dbo · **Cluster**: Other · **Rows**: 252 · **Size**: 0.13 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloSvetla` | int | NE |  |  |
| 3 | `CisloSkupiny` | int | NE |  |  |
| 4 | `Poznamka` | nvarchar(200) | NE |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE |  |  |
| 7 | `Zmenil` | nchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
