# EC_PrehledyFiltryUziv

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.01 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `FieldName` | nvarchar(50) | NE |  |  |
| 4 | `Hodnota` | nvarchar(50) | NE |  |  |
| 5 | `CisloPrehleduCil` | int | ANO |  |  |
| 6 | `CisloPrehleduZdroj` | int | ANO |  |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Trvaly` | bit | ANO | ((0)) |  |
| 9 | `CisloOrg` | int | ANO |  |  |
| 10 | `ZobrazitMaterial` | bit | ANO | ((1)) |  |
| 11 | `ZobrazitSluzby` | bit | ANO | ((1)) |  |
