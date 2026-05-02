# EC_Fotky_Archiv

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDZdroj` | int | ANO |  |  |
| 3 | `Nazev_Zdroj` | nvarchar(50) | ANO |  |  |
| 4 | `Nazev_Cil` | nvarchar(50) | ANO |  |  |
| 5 | `Cesta_Zdroj` | nvarchar(100) | ANO |  |  |
| 6 | `Cesta_Cil` | nvarchar(100) | ANO |  |  |
| 7 | `IDZarizeni` | nvarchar(100) | ANO |  |  |
| 8 | `DatPorizeni_Zdroj` | datetime | ANO |  |  |
| 9 | `DatSynchronizace` | datetime | ANO |  |  |
| 10 | `Autor_Zdroj` | nvarchar(10) | ANO |  |  |
| 11 | `Synchronizoval` | nvarchar(10) | ANO |  |  |
| 12 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 13 | `Typ` | tinyint | ANO |  |  |
| 14 | `FileExists` | bit | ANO |  |  |
| 15 | `AppNazev` | nvarchar(100) | ANO |  |  |
| 16 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 17 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 18 | `Archivoval` | nvarchar(10) | ANO | (suser_sname()) |  |
