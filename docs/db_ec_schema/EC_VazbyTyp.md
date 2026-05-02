# EC_VazbyTyp

**Schema**: dbo · **Cluster**: Other · **Rows**: 22 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Zkratka` | nvarchar(100) | ANO |  |  |
| 3 | `NazevTabulky` | nvarchar(100) | ANO |  |  |
| 4 | `Popis` | nvarchar(255) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `ID_E` | int | ANO |  |  |
