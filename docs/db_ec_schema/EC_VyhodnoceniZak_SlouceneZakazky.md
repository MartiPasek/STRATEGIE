# EC_VyhodnoceniZak_SlouceneZakazky

**Schema**: dbo · **Cluster**: Other · **Rows**: 82 · **Size**: 0.09 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazkyZdroj` | nvarchar(10) | ANO |  |  |
| 3 | `CisloZakazkyCil` | nvarchar(10) | ANO |  |  |
| 4 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
