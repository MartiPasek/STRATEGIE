# EC_Zakazky_KontrolaFakturace

**Schema**: dbo · **Cluster**: Finance · **Rows**: 4,774 · **Size**: 2.38 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `typDokladu` | varchar(7) | ANO |  |  |
| 2 | `IDZak` | int | ANO |  |  |
| 3 | `ID` | int | ANO |  |  |
| 4 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 5 | `Zakaznik` | nvarchar(15) | ANO |  |  |
| 6 | `Resitel` | nvarchar(128) | ANO |  |  |
| 7 | `DatumPorizeni` | datetime | ANO |  |  |
| 8 | `Mena` | varchar(3) | ANO |  |  |
| 9 | `ObjSumaVal` | numeric(38,6) | ANO |  |  |
| 10 | `ObjSumaKc` | numeric(38,6) | ANO |  |  |
| 11 | `FaSumaKc` | numeric(38,6) | ANO |  |  |
| 12 | `FaSumaVal` | numeric(38,6) | ANO |  |  |
| 13 | `FaMena` | varchar(3) | ANO |  |  |
| 14 | `Ukonceno` | tinyint | ANO |  |  |
| 15 | `PocetFA` | int | ANO |  |  |
| 16 | `PocetRealizovano` | int | ANO |  |  |
| 17 | `ChybiFakturace` | int | ANO |  |  |
| 18 | `StavFakturace` | varchar(21) | ANO |  |  |
| 19 | `Uhrazeno` | nvarchar(20) | ANO | (N'Neuhrazeno') |  |
| 20 | `NazevZakazky` | nvarchar(200) | ANO |  |  |
| 21 | `DruhyNazevZakazky` | nvarchar(200) | ANO |  |  |
