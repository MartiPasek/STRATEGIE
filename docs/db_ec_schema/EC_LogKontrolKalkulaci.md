# EC_LogKontrolKalkulaci

**Schema**: dbo · **Cluster**: Logging · **Rows**: 103,255 · **Size**: 15.64 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `TypKontroly` | nvarchar(100) | ANO |  |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `ZacatekKontroly` | bit | ANO |  |  |
| 6 | `KonecKontroly` | bit | ANO |  |  |
| 7 | `Poznamka` | nchar(10) | ANO |  |  |
