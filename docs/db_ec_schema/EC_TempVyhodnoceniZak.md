# EC_TempVyhodnoceniZak

**Schema**: dbo · **Cluster**: Other · **Rows**: 14,838 · **Size**: 4.63 MB · **Sloupců**: 36 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `CisloZam` | int | ANO |  |  |
| 2 | `PocetHodin` | numeric(19,6) | ANO |  |  |
| 3 | `Kalkulovano` | numeric(19,6) | ANO |  |  |
| 4 | `KalkulovanoRevize` | numeric(19,6) | ANO |  |  |
| 5 | `SumaOdpracovano` | numeric(19,6) | ANO |  |  |
| 6 | `LimitProSrazku` | numeric(19,6) | ANO |  |  |
| 7 | `PremieZakazky` | numeric(19,6) | ANO |  |  |
| 8 | `PremieOsoba` | numeric(19,6) | ANO |  |  |
| 9 | `UsetrenyCasOsoba` | numeric(19,6) | ANO |  |  |
| 10 | `UsetrenyCasCelkem` | numeric(19,6) | ANO |  |  |
| 11 | `PretazenyCasCelkem` | numeric(19,6) | ANO |  |  |
| 12 | `PretazenyCasOsoba` | numeric(19,6) | ANO |  |  |
| 13 | `SrazkaOsoba` | numeric(19,6) | ANO |  |  |
| 14 | `EfektivitaOsoba` | numeric(19,6) | ANO | ((100)) |  |
| 15 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 16 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 17 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 18 | `PremieOsobaFinal` | numeric(36,6) | ANO |  |  |
| 19 | `PremieOsobaEf` | numeric(19,6) | ANO |  |  |
| 20 | `PremieSefmonter` | numeric(19,6) | ANO |  |  |
| 21 | `Sefmonter` | bit | ANO |  |  |
| 22 | `PremieOsobaSpec` | numeric(19,6) | ANO |  |  |
| 23 | `PoznamkaVV` | nvarchar(500) | ANO |  |  |
| 24 | `PoznamkaVP` | nvarchar(500) | ANO |  |  |
| 25 | `PoznamkaSefmonter` | nvarchar(500) | ANO |  |  |
| 26 | `PremieSrazkaSerie` | numeric(38,6) | ANO |  |  |
| 27 | `SrazkaSerieProcenta` | int | ANO |  |  |
| 28 | `Flexibilita` | tinyint | ANO | ((1)) |  |
| 29 | `FlexibilitaPoznamka` | nvarchar(4000) | ANO |  |  |
| 30 | `Chybovost` | tinyint | ANO | ((1)) |  |
| 31 | `ChybovostPoznamka` | nvarchar(4000) | ANO |  |  |
| 32 | `Estetika` | tinyint | ANO | ((1)) |  |
| 33 | `EstetikaPoznamka` | nvarchar(4000) | ANO |  |  |
| 34 | `ID` | int | NE |  |  |
| 35 | `ZkusebnaPoznamka` | nvarchar(4000) | ANO |  |  |
| 36 | `NepodepsanyZakList` | bit | ANO | ((0)) |  |
