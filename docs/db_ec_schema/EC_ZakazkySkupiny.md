# EC_ZakazkySkupiny

**Schema**: dbo · **Cluster**: Finance · **Rows**: 231 · **Size**: 0.14 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(200) | ANO |  |  |
| 3 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 5 | `Typ` | smallint | ANO | ((1)) |  |
