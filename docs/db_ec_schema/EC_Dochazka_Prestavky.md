# EC_Dochazka_Prestavky

**Schema**: dbo · **Cluster**: HR · **Rows**: 65,160 · **Size**: 6.39 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CasZacatek` | datetime | ANO |  |  |
| 3 | `CasKonec` | datetime | ANO |  |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `DruhCinnosti` | int | ANO |  |  |
| 6 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `MACAdress` | nvarchar(100) | ANO |  |  |
| 10 | `ReziePoznamka` | varchar(80) | ANO |  |  |
| 11 | `ZamPoznamka` | varchar(80) | ANO |  |  |
| 12 | `PozadPomocVed` | bit | ANO | ((0)) |  |
| 13 | `SefMontPoznamka` | varchar(80) | ANO |  |  |
| 14 | `VedPoznamka` | varchar(80) | ANO |  |  |
| 15 | `DatumPripadu` | datetime | ANO | (getdate()) |  |
| 16 | `CisloZakazky` | varchar(15) | ANO |  |  |
| 17 | `VedSchvaleno` | bit | ANO |  |  |
| 18 | `IDEventImp` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Dochazka_Prestavky` (CLUSTERED) — `ID`
- **INDEX** `IxE_EC_Dochazka_Prestavky_CisloZam_CasZacatek_CasKonec` (NONCLUSTERED) — `DruhCinnosti, DatumPripadu, CisloZam, CasZacatek, CasKonec`
