# EC_Dochazka_ARCHIV

**Schema**: dbo · **Cluster**: HR · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 58 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumPripadu` | datetime | NE |  |  |
| 3 | `DenVTydnu` | nvarchar(50) | ANO |  |  |
| 4 | `CisloZam` | int | NE |  |  |
| 5 | `DruhCinnosti` | smallint | NE |  |  |
| 6 | `CisloZakazky` | varchar(15) | NE |  |  |
| 7 | `CasZacatek` | datetime | ANO |  |  |
| 8 | `CasKonec` | datetime | ANO |  |  |
| 9 | `CasPauza` | int | NE |  |  |
| 10 | `CasBlbost` | int | NE |  |  |
| 11 | `CasRezie` | int | NE |  |  |
| 12 | `ReziePoznamka` | varchar(80) | ANO |  |  |
| 13 | `ZamPoznamka` | varchar(200) | ANO |  |  |
| 14 | `PozadPomocVed` | bit | ANO |  |  |
| 15 | `SefMontPoznamka` | varchar(80) | ANO |  |  |
| 16 | `VedPoznamka` | varchar(80) | ANO |  |  |
| 17 | `CasPausaKorSefMont` | int | NE |  |  |
| 18 | `CasPausaKorVed` | int | ANO |  |  |
| 19 | `VedSchvaleno` | bit | ANO |  |  |
| 20 | `SefSchvaleno` | bit | ANO |  |  |
| 21 | `CasCelkemZakazka` | numeric(18,0) | ANO |  |  |
| 22 | `CasCelkemVcRezii` | numeric(18,0) | ANO |  |  |
| 23 | `PraceAktivni` | bit | NE |  |  |
| 24 | `HeliosID` | bit | NE |  |  |
| 25 | `Hod_Predpoklad_Kc` | int | ANO |  |  |
| 26 | `Hod_Real_Kc` | int | ANO |  |  |
| 27 | `Kc_Predpoklad` | numeric(18,0) | ANO |  |  |
| 28 | `Kc_Real` | numeric(18,0) | ANO |  |  |
| 29 | `DatumZaplaceni` | datetime | ANO |  |  |
| 30 | `FormaZaplaceni` | tinyint | ANO |  |  |
| 31 | `DenZacatek` | datetime | ANO |  |  |
| 32 | `HodinyDoFPD` | numeric(18,2) | NE |  |  |
| 33 | `Prevedeno` | numeric(18,2) | NE |  |  |
| 34 | `ProplatitPremii` | numeric(18,2) | NE |  |  |
| 35 | `StavCasKonta` | numeric(18,2) | NE |  |  |
| 36 | `ZaklMzda` | numeric(18,2) | NE |  |  |
| 37 | `PremieKc` | numeric(18,2) | NE |  |  |
| 38 | `FinanceZakazka` | numeric(18,2) | NE |  |  |
| 39 | `OdmenazFinanciZak` | numeric(18,2) | NE |  |  |
| 40 | `Poznamka` | nvarchar(250) | ANO |  |  |
| 41 | `Status` | int | NE |  |  |
| 42 | `DatumPripadu_M` | int | ANO |  |  |
| 43 | `DatumPripadu_Y` | int | ANO |  |  |
| 44 | `DruhCinn_Mzdy` | int | NE |  |  |
| 45 | `DatumPripadu_DMR` | datetime | ANO |  |  |
| 46 | `VykonPremieKc` | numeric(18,2) | ANO |  |  |
| 47 | `LoginFrom` | nvarchar(1) | ANO |  |  |
| 48 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 49 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 50 | `Montaz` | bit | ANO |  |  |
| 51 | `Uzavreno` | bit | ANO |  |  |
| 52 | `Archivoval` | nvarchar(126) | ANO |  |  |
| 53 | `DatArchivace` | datetime | ANO |  |  |
| 54 | `cascelkemInterni` | numeric(9,2) | ANO |  |  |
| 55 | `Kc_Hod_FinPodm` | numeric(9,2) | ANO |  |  |
| 56 | `Kc_Celkem` | numeric(9,2) | ANO |  |  |
| 57 | `IDPolVOBJ` | int | ANO |  |  |
| 58 | `IDPolPF` | int | ANO |  |  |
