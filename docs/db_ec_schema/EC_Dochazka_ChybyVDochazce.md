# EC_Dochazka_ChybyVDochazce

**Schema**: dbo · **Cluster**: HR · **Rows**: 49,152 · **Size**: 6.52 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `Typ` | int | ANO |  |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `IDDoch` | int | ANO |  |  |
| 6 | `IDSumaDen` | int | ANO |  |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatumPripadu` | datetime | ANO |  |  |
| 10 | `ChybaJeOK` | bit | ANO | ((0)) |  |
| 11 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 12 | `ChybuPotvrdil` | nvarchar(126) | ANO |  |  |
| 13 | `DatPotvrzeni` | datetime | ANO |  |  |
