# EC_Dochazka_PrevodPrescasu_Archiv

**Schema**: dbo · **Cluster**: HR · **Rows**: 16,519 · **Size**: 5.95 MB · **Sloupců**: 26 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `NoveDatum` | varchar(10) | ANO |  |  |
| 2 | `PrijmeniJmeno` | nvarchar(201) | ANO |  |  |
| 3 | `ZacatekPuvodni` | datetime | ANO |  |  |
| 4 | `KonecPuvodni` | datetime | ANO |  |  |
| 5 | `ZacatekNovy` | datetime | ANO |  |  |
| 6 | `konecNovy` | datetime | ANO |  |  |
| 7 | `ID` | int | NE |  |  |
| 8 | `PrescasZbyva` | numeric(19,2) | ANO |  |  |
| 9 | `Provedl` | nvarchar(128) | ANO |  |  |
| 10 | `DatProvedeni` | datetime | NE |  |  |
| 11 | `CisloZam` | int | NE |  |  |
| 12 | `ZamPoznamka` | varchar(1000) | ANO |  |  |
| 13 | `VedPoznamka` | varchar(1000) | ANO |  |  |
| 14 | `Poznamka` | nvarchar(1000) | ANO |  |  |
| 15 | `PraceAktivni` | bit | NE |  |  |
| 16 | `LoginFrom` | nvarchar(1) | ANO |  |  |
| 17 | `CasPauza` | int | NE |  |  |
| 18 | `CasBlbost` | int | NE |  |  |
| 19 | `DruhCinnosti` | smallint | NE |  |  |
| 20 | `CisloZakazky` | varchar(15) | NE |  |  |
| 21 | `DatumPripadu` | datetime | NE |  |  |
| 22 | `CasZacatekOrig` | datetime | ANO |  |  |
| 23 | `CasKonecOrig` | datetime | ANO |  |  |
| 24 | `Autor` | nvarchar(128) | ANO |  |  |
| 25 | `DatPorizeni` | datetime | ANO |  |  |
| 26 | `Typ` | nvarchar(100) | ANO |  |  |
