# EC_PohybyZbozi_VyberUziv

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 7 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | ANO |  |  |
| 2 | `SumujDleDilu` | bit | NE | ((0)) |  |
| 3 | `DatumOd` | datetime | ANO |  |  |
| 4 | `DatumDo` | datetime | ANO |  |  |
| 5 | `DruhPohybu` | int | ANO |  |  |
| 6 | `RadaDokladu` | int | ANO |  |  |
| 7 | `RegCis` | nvarchar(50) | ANO |  |  |
| 8 | `CisloOrg` | int | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
