# EC_Pozadavky_seznam

**Schema**: dbo · **Cluster**: Other · **Rows**: 4 · **Size**: 0.07 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 4 | `datporizeni` | datetime | ANO | (getdate()) |  |
| 5 | `IDPredlohyUkolu` | int | ANO |  |  |
