# EC_SeznamMistnosti

**Schema**: dbo · **Cluster**: Other · **Rows**: 26 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 4 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 5 | `Aktualni` | bit | NE | ((1)) |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
