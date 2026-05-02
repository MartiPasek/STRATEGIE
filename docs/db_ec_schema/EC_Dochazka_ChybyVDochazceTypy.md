# EC_Dochazka_ChybyVDochazceTypy

**Schema**: dbo · **Cluster**: HR · **Rows**: 23 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `ID_E` | int | ANO |  |  |
