# EC_Dochazka

**Schema**: dbo · **Cluster**: HR · **Rows**: 393,160 · **Size**: 108.15 MB · **Sloupců**: 63 · **FK**: 0 · **Indexů**: 10

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumPripadu` | datetime | NE | (getdate()) |  |
| 3 | `DenVTydnu` | nvarchar(2) | ANO |  |  |
| 4 | `CisloZam` | int | NE |  |  |
| 5 | `DruhCinnosti` | smallint | NE | ((6)) |  |
| 6 | `CisloZakazky` | varchar(15) | NE |  |  |
| 7 | `CasZacatek` | datetime | ANO | (dateadd(second,(60)-datepart(second,getdate()),getdate())) |  |
| 8 | `CasKonec` | datetime | ANO |  |  |
| 9 | `CasPauza` | int | NE | ((0)) |  |
| 10 | `CasBlbost` | int | NE | ((0)) |  |
| 11 | `CasRezie` | int | NE | ((0)) |  |
| 12 | `ReziePoznamka` | varchar(80) | ANO |  |  |
| 13 | `ZamPoznamka` | varchar(200) | ANO |  |  |
| 14 | `PozadPomocVed` | bit | ANO |  |  |
| 15 | `SefMontPoznamka` | varchar(80) | ANO |  |  |
| 16 | `VedPoznamka` | varchar(80) | ANO |  |  |
| 17 | `CasPausaKorSefMont` | int | NE | ((0)) |  |
| 18 | `CasPausaKorVed` | int | ANO | ((0)) |  |
| 19 | `VedSchvaleno` | bit | ANO |  |  |
| 20 | `SefSchvaleno` | bit | ANO |  |  |
| 21 | `CasCelkemZakazka` | numeric(17,6) | ANO |  |  |
| 22 | `CasCelkemVcRezii` | numeric(17,6) | ANO |  |  |
| 23 | `PraceAktivni` | bit | NE | ((1)) |  |
| 24 | `HeliosID` | bit | NE | ((0)) |  |
| 25 | `Hod_Predpoklad_Kc` | int | ANO |  |  |
| 26 | `Hod_Real_Kc` | int | ANO |  |  |
| 27 | `Kc_Predpoklad` | numeric(28,6) | ANO |  |  |
| 28 | `Kc_Real` | numeric(28,6) | ANO |  |  |
| 29 | `DatumZaplaceni` | datetime | ANO |  |  |
| 30 | `FormaZaplaceni` | tinyint | ANO |  |  |
| 31 | `DenZacatek` | datetime | ANO |  |  |
| 32 | `HodinyDoFPD` | numeric(18,2) | NE | ((0)) | Hodiny, které jsou vzplacené zaměstnanci v rámci fondu prac.doby. Příklad - v měsíci je 20 prac.dní á 8 hod,tj.FPD 160 h |
| 33 | `Prevedeno` | numeric(18,2) | NE | ((0)) |  |
| 34 | `ProplatitPremii` | numeric(18,2) | NE | ((0)) |  |
| 35 | `StavCasKonta` | numeric(18,2) | NE | ((0)) |  |
| 36 | `ZaklMzda` | numeric(18,2) | NE | ((0)) |  |
| 37 | `PremieKc` | numeric(18,2) | NE | ((0)) |  |
| 38 | `FinanceZakazka` | numeric(18,2) | NE | ((0)) |  |
| 39 | `OdmenazFinanciZak` | numeric(18,2) | NE | ((0)) |  |
| 40 | `Poznamka` | nvarchar(250) | ANO |  |  |
| 41 | `Status` | int | NE | ((0)) | 0..pořízeno, 1 .. změna 2..přepočítáno,9 uzavřeno |
| 42 | `DatumPripadu_M` | int | ANO |  |  |
| 43 | `DatumPripadu_Y` | int | ANO |  |  |
| 44 | `DruhCinn_Mzdy` | int | NE |  |  |
| 45 | `DatumPripadu_DMR` | datetime | ANO |  |  |
| 46 | `VykonPremieKc` | numeric(18,2) | ANO |  |  |
| 47 | `LoginFrom` | nvarchar(1) | ANO |  |  |
| 48 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 49 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 50 | `Montaz` | bit | ANO | ((0)) |  |
| 51 | `Uzavreno` | bit | ANO | ((0)) |  |
| 52 | `Kc_Hod_FinPodm` | numeric(9,2) | ANO |  |  |
| 53 | `Kc_Celkem` | numeric(9,2) | ANO |  |  |
| 54 | `IDEventImp` | int | ANO | ((0)) |  |
| 55 | `IDPolVOBJ` | int | ANO |  |  |
| 56 | `IDPolPF` | int | ANO |  |  |
| 57 | `CasCelkemInterni` | numeric(17,6) | ANO |  |  |
| 58 | `CasCelkemInterniOld` | numeric(9,2) | ANO |  |  |
| 59 | `DatZmeny` | datetime | ANO |  |  |
| 60 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 61 | `MACAdress` | nvarchar(100) | ANO |  |  |
| 62 | `PrevodPrescasu` | bit | ANO | ((0)) |  |
| 63 | `Import` | bit | NE | ((0)) |  |

## Indexy

- **PK** `PK_EC_Dochazka` (CLUSTERED) — `ID`
- **INDEX** `IX_Dochazka_ByCisloZam` (NONCLUSTERED) — `DatumPripadu, DruhCinnosti, CisloZakazky, CasZacatek, CasKonec, CisloZam`
- **INDEX** `IX_EC_Dochazka_DruhCinnostiCisloZakazkyCasZacatek` (NONCLUSTERED) — `DruhCinnosti, CisloZakazky, CasZacatek`
- **INDEX** `DruhCinnosti_Includes` (NONCLUSTERED) — `CisloZam, DatPorizeni, DatZmeny, DruhCinnosti`
- **INDEX** `CisloZam_DruhCinnosti_CasZacatek_Includes` (NONCLUSTERED) — `DatumPripadu, CisloZakazky, ZamPoznamka, PraceAktivni, CisloZam, DruhCinnosti, CasZacatek`
- **INDEX** `CisloZam_PraceAktivni` (NONCLUSTERED) — `CisloZam, PraceAktivni`
- **INDEX** `CisloZam_PraceAktivni_Includes` (NONCLUSTERED) — `DatumPripadu, DruhCinnosti, CisloZakazky, CisloZam, PraceAktivni`
- **INDEX** `PraceAktivni_CisloZam_LoginFrom_Includes` (NONCLUSTERED) — `DatumPripadu, DruhCinnosti, CisloZakazky, PraceAktivni, CisloZam, LoginFrom`
- **INDEX** `IxE_EC_Dochazka_CisloZam_CasZacatek_CasCelkemZakazka` (NONCLUSTERED) — `DruhCinnosti, CisloZam, CasZacatek, CasCelkemZakazka`
- **INDEX** `ix_ecDochazka_CisloZakazky` (NONCLUSTERED) — `CisloZakazky`
