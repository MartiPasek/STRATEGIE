# EC_Logovani

**Schema**: dbo · **Cluster**: Logging · **Rows**: 12,728 · **Size**: 11.83 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Procedura` | nvarchar(50) | ANO |  |  |
| 3 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime2 | NE | (getdate()) |  |
| 6 | `Text` | ntext | ANO |  |  |
