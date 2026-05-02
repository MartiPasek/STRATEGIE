# EC_ZakazkyZisk_VysvetleniSeznam

**Schema**: dbo · **Cluster**: Finance · **Rows**: 14 · **Size**: 0.07 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Vysvetleni` | nvarchar(500) | ANO |  |  |
| 3 | `Typ` | int | ANO |  |  |
| 4 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
