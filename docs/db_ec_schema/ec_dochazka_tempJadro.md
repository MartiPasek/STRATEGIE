# ec_dochazka_tempJadro

**Schema**: dbo · **Cluster**: Other · **Rows**: 94 · **Size**: 0.15 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | ANO |  |  |
| 2 | `Novy` | bit | ANO |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `DatumPripadu` | date | ANO |  |  |
| 5 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 6 | `DruhCinnosti` | int | ANO |  |  |
| 7 | `VedPoznamka` | nvarchar(1000) | ANO |  |  |
| 8 | `ZamPoznamka` | nvarchar(1000) | ANO |  |  |
| 9 | `CasZacatek` | datetime | ANO |  |  |
| 10 | `CasKonec` | datetime | ANO |  |  |
| 11 | `CasPauza` | int | ANO |  |  |
| 12 | `CasBlbost` | int | ANO |  |  |
| 13 | `CasRezie` | int | ANO |  |  |
| 14 | `Poznamka` | nvarchar(1000) | ANO |  |  |
| 15 | `SefmontPoznamka` | nvarchar(1000) | ANO |  |  |
| 16 | `ReziePoznamka` | nvarchar(1000) | ANO |  |  |
| 17 | `PozadPomocVed` | bit | ANO |  |  |
| 18 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 19 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 20 | `VedSchvaleno` | bit | ANO |  |  |
