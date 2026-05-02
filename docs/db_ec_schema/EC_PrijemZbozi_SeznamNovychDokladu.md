# EC_PrijemZbozi_SeznamNovychDokladu

**Schema**: dbo · **Cluster**: Other · **Rows**: 8 · **Size**: 0.20 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | ANO |  |  |
| 2 | `ID_E` | int | ANO |  |  |
| 3 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 4 | `DatPorizeni` | nchar(10) | ANO | (getdate()) |  |
| 5 | `Poznamka` | nvarchar(1000) | ANO |  |  |
