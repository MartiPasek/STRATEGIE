# EC_ZakazkyHodNavic_Vzor

**Schema**: dbo · **Cluster**: Finance · **Rows**: 13 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DuvodNavyseni` | nvarchar(100) | ANO |  |  |
| 3 | `autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 5 | `PocetHodin` | smallint | ANO |  |  |
| 6 | `PocetMinut` | smallint | ANO |  |  |
| 7 | `Poznamka` | nvarchar(255) | ANO |  |  |
