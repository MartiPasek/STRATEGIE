# EC_KontrolySeznam

**Schema**: dbo · **Cluster**: Other · **Rows**: 106 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Procedura` | nvarchar(200) | ANO |  |  |
| 4 | `DatZalozeni` | datetime | ANO | (getdate()) |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 7 | `OdesliVedoucimu` | bit | NE | ((0)) |  |
