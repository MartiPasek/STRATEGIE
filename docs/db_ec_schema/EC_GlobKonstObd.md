# EC_GlobKonstObd

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `PlatnostOd` | datetime | ANO | (getdate()) |  |
| 3 | `PlatnostDo` | datetime | ANO |  |  |
| 4 | `CastkaStravenky` | numeric(9,2) | ANO |  |  |
| 5 | `SlevaNaDani` | numeric(9,2) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
