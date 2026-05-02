# EC_SeznamSkrini

**Schema**: dbo · **Cluster**: Other · **Rows**: 560 · **Size**: 0.13 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `CisloDod` | nvarchar(80) | ANO |  |  |
| 2 | `Sirka` | int | ANO |  |  |
| 3 | `Vyska` | int | ANO |  |  |
| 4 | `Hloubka` | int | ANO |  |  |
| 5 | `Typ` | nvarchar(80) | ANO |  |  |
| 6 | `Vyrobce` | nvarchar(80) | ANO |  |  |
| 7 | `RegCis` | nvarchar(126) | ANO |  |  |
| 8 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `ID` | int | ANO |  |  |
| 11 | `PocetEuPalte` | numeric(18,6) | ANO | ((0)) |  |
| 12 | `PocetRittalPalet` | numeric(18,6) | ANO | ((0)) |  |
| 13 | `PocetMensichPalet` | numeric(18,6) | ANO | ((0)) |  |
| 17 | `CIsloOrg` | int | ANO | ((0)) |  |
