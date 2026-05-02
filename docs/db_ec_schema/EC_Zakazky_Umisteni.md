# EC_Zakazky_Umisteni

**Schema**: dbo · **Cluster**: Finance · **Rows**: 1,280 · **Size**: 0.21 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDUmisteni` | int | ANO |  |  |
| 3 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 4 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
