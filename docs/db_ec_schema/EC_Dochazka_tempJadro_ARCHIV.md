# EC_Dochazka_tempJadro_ARCHIV

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 24 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDDoch` | int | ANO |  |  |
| 3 | `Novy` | bit | ANO |  |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `DatumPripadu` | date | ANO |  |  |
| 6 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 7 | `DruhCinnosti` | int | ANO |  |  |
| 8 | `VedPoznamka` | nvarchar(1000) | ANO |  |  |
| 9 | `ZamPoznamka` | nvarchar(1000) | ANO |  |  |
| 10 | `CasZacatek` | datetime | ANO |  |  |
| 11 | `CasKonec` | datetime | ANO |  |  |
| 12 | `CasPauza` | int | ANO |  |  |
| 13 | `CasBlbost` | int | ANO |  |  |
| 14 | `CasRezie` | int | ANO |  |  |
| 15 | `Poznamka` | nvarchar(1000) | ANO |  |  |
| 16 | `SefmontPoznamka` | nvarchar(1000) | ANO |  |  |
| 17 | `ReziePoznamka` | nvarchar(1000) | ANO |  |  |
| 18 | `PozadPomocVed` | bit | ANO |  |  |
| 19 | `Autor` | nvarchar(128) | ANO |  |  |
| 20 | `DatPorizeni` | datetime | ANO |  |  |
| 21 | `VedSchvaleno` | bit | ANO |  |  |
| 22 | `Archivoval` | nvarchar(126) | ANO | (suser_sname()) |  |
| 23 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 24 | `PoznamkaArchivace` | nvarchar(1000) | ANO |  |  |
