# EC_Zakazky_PlatbyZamHlav

**Schema**: dbo · **Cluster**: Finance · **Rows**: 5,348 · **Size**: 0.53 MB · **Sloupců**: 4 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
