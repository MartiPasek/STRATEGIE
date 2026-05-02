# EC_VytizeniSkupiny

**Schema**: dbo · **Cluster**: Production · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 4 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(200) | ANO |  |  |
| 3 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
