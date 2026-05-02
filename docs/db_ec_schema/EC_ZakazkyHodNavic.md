# EC_ZakazkyHodNavic

**Schema**: dbo · **Cluster**: Finance · **Rows**: 3,667 · **Size**: 1.30 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `PocetHodin` | numeric(19,2) | ANO |  |  |
| 3 | `CisloZakazky` | nvarchar(10) | NE |  |  |
| 4 | `DuvodNavyseni` | nvarchar(200) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Typ` | smallint | NE |  | 1 = Zadal VP, 2 = Zadal vedoucí výroby |
| 8 | `Schvalil` | nvarchar(15) | ANO |  |  |
| 9 | `DatSchvaleni` | datetime | ANO |  |  |
| 10 | `PocetHodinZadost` | numeric(19,2) | ANO |  |  |
| 11 | `Poznamka` | nvarchar(255) | ANO |  |  |
| 12 | `PoznamkaSchvaleni` | nvarchar(255) | ANO |  |  |
| 13 | `VProcentech` | bit | ANO | ((0)) |  |
