# EC_LogKalkGenDoklad

**Schema**: dbo · **Cluster**: Logging · **Rows**: 9,644 · **Size**: 1.93 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `TypDokladu` | nvarchar(100) | ANO |  |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `Mode` | int | ANO |  |  |
| 6 | `Poznamka` | nchar(10) | ANO |  |  |
