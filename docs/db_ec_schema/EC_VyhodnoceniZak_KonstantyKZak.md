# EC_VyhodnoceniZak_KonstantyKZak

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,789 · **Size**: 1.11 MB · **Sloupců**: 33 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `SazbaPremie` | numeric(6,2) | ANO |  |  |
| 3 | `SazbaSrazka` | numeric(6,2) | ANO |  |  |
| 4 | `KonstCasRezerva` | numeric(5,2) | ANO |  |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(126) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `PremieSefmonterHod` | numeric(19,6) | ANO |  |  |
| 10 | `PremieSefmonter` | numeric(19,6) | ANO |  |  |
| 11 | `PremieSefmonterKoef` | numeric(19,6) | ANO |  |  |
| 12 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 13 | `NazevZakazkyTisk` | nvarchar(200) | ANO |  |  |
| 14 | `UzavrenoKDatu` | date | ANO |  |  |
| 15 | `KalkHodiny` | numeric(19,6) | ANO |  |  |
| 16 | `KalkHodinyCelkem` | numeric(19,6) | ANO |  |  |
| 17 | `SrazkaSerie` | numeric(19,6) | ANO |  |  |
| 18 | `Odpracovano` | numeric(19,6) | ANO |  |  |
| 19 | `OdpracovanoEF` | numeric(19,6) | ANO |  |  |
| 20 | `KalkHodNavicCislo` | numeric(19,6) | ANO |  |  |
| 21 | `KalkHodNavicProcento` | numeric(19,6) | ANO |  |  |
| 22 | `PlanovanoSuma` | numeric(19,6) | ANO |  |  |
| 23 | `CelkemSPremiemi` | numeric(19,6) | ANO |  |  |
| 24 | `PremieCelkem` | numeric(19,6) | ANO |  |  |
| 25 | `LimitProSrazku` | numeric(19,6) | ANO |  |  |
| 26 | `UsetrenoHodin` | numeric(19,6) | ANO |  |  |
| 27 | `PretazenoHod` | numeric(19,6) | ANO |  |  |
| 28 | `PretazenoProc` | numeric(19,6) | ANO |  |  |
| 29 | `EfektivitaPridatHodiny` | numeric(19,6) | ANO |  |  |
| 30 | `KalkHodCelkemSEf` | numeric(19,6) | ANO |  |  |
| 31 | `ListZakazek` | nvarchar(1000) | ANO |  |  |
| 32 | `KoefVyrobaKalkHod` | numeric(19,6) | ANO |  |  |
| 33 | `KalkHodVyroba` | numeric(19,6) | ANO |  |  |
