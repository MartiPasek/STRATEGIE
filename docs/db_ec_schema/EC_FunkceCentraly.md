# EC_FunkceCentraly

**Schema**: dbo · **Cluster**: Other · **Rows**: 36 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `NazevFunkce` | nvarchar(100) | NE |  |  |
| 3 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 4 | `Kategorie` | nvarchar(30) | ANO |  |  |
| 5 | `Firma` | nvarchar(10) | ANO |  |  |
| 6 | `DatumZahajeniProvozu` | datetime | ANO |  |  |
| 7 | `Vyvojar` | nvarchar(20) | ANO |  |  |
| 8 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
