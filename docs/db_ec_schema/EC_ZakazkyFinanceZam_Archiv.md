# EC_ZakazkyFinanceZam_Archiv

**Schema**: dbo · **Cluster**: Finance · **Rows**: 623 · **Size**: 0.28 MB · **Sloupců**: 29 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPuvodni` | int | ANO |  |  |
| 3 | `DatumPorizeni` | datetime | ANO |  |  |
| 4 | `CisloZakazky` | varchar(15) | ANO |  |  |
| 5 | `CisloZam` | int | ANO |  |  |
| 6 | `HodSazba` | int | ANO |  |  |
| 7 | `FixPremie` | int | ANO |  |  |
| 8 | `PocetHodin` | numeric(8,2) | ANO |  |  |
| 9 | `PenizeCelkem` | numeric(12,2) | ANO |  |  |
| 10 | `Uzavreno` | bit | ANO |  |  |
| 11 | `Vyplatit` | int | ANO |  |  |
| 12 | `Vyplaceno` | int | ANO |  |  |
| 13 | `ZbyvaVyplatit` | numeric(12,2) | ANO |  |  |
| 14 | `DatPosledniPlatby` | datetime | ANO |  |  |
| 15 | `Efektivita` | int | ANO |  |  |
| 16 | `PoznamkaVV` | nvarchar(500) | ANO |  |  |
| 17 | `PoznamkaVP` | nvarchar(500) | ANO |  |  |
| 18 | `PoznamkaSefmonter` | nvarchar(500) | ANO |  |  |
| 19 | `Autor` | nvarchar(10) | ANO |  |  |
| 20 | `IDPolVobj` | int | ANO |  |  |
| 21 | `IDPolPF` | int | ANO |  |  |
| 22 | `Archivoval` | nvarchar(126) | ANO | (suser_sname()) |  |
| 23 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 24 | `Sefmonter` | bit | ANO |  |  |
| 25 | `PremieOsobaSpec` | numeric(19,6) | ANO |  |  |
| 26 | `PremieSefmonter` | numeric(19,6) | ANO |  |  |
| 27 | `PremieOsobaFinal` | numeric(19,6) | ANO |  |  |
| 28 | `PremieOsobaEf` | numeric(19,6) | ANO |  |  |
| 29 | `SrazkaOsoba` | numeric(19,6) | ANO |  |  |
