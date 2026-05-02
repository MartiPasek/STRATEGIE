# EC_PotvrzeniVOBJ_Archiv

**Schema**: dbo · **Cluster**: Other · **Rows**: 684 · **Size**: 0.34 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPol` | int | ANO |  |  |
| 3 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 4 | `Archivoval` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `PuvodniPotvrzDatDod` | datetime | ANO |  |  |
| 6 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 7 | `IDDoklad` | int | ANO |  |  |
