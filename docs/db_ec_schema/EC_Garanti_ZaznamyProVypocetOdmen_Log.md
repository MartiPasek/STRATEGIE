# EC_Garanti_ZaznamyProVypocetOdmen_Log

**Schema**: dbo · **Cluster**: Finance · **Rows**: 752 · **Size**: 0.48 MB · **Sloupců**: 24 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID_master` | int | NE |  |  |
| 2 | `ID` | int | ANO |  |  |
| 3 | `SloucenaZakazka` | bit | ANO |  |  |
| 4 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 5 | `Zkratka` | nvarchar(15) | ANO |  |  |
| 6 | `Nazev` | nvarchar(100) | ANO |  |  |
| 7 | `DruhyNazev` | nvarchar(100) | ANO |  |  |
| 8 | `Resitel` | nvarchar(128) | ANO |  |  |
| 9 | `_Sefmonter` | nvarchar(20) | ANO |  |  |
| 10 | `kalkulovanoCelkem` | smallint | ANO |  |  |
| 11 | `_RealHodiny` | int | ANO |  |  |
| 12 | `EfektivniHodiny` | numeric(19,6) | ANO |  |  |
| 13 | `DatPorizeni` | datetime | ANO |  |  |
| 14 | `autor` | nvarchar(128) | ANO |  |  |
| 15 | `DatumKonecReal` | datetime | ANO |  |  |
| 16 | `DatumKonecPlan` | datetime | ANO |  |  |
| 17 | `_VyhodnoceniUzavreno` | bit | ANO |  |  |
| 18 | `Zacatek` | datetime | ANO |  |  |
| 19 | `Konec` | datetime | ANO |  |  |
| 20 | `_PocetKsMalyRozvadec` | numeric(19,6) | ANO |  |  |
| 21 | `_PocetKsVelkyRozvadec` | numeric(19,6) | ANO |  |  |
| 22 | `Garant` | nvarchar(201) | ANO |  |  |
| 23 | `Autor_master` | nvarchar(128) | NE | (suser_name()) |  |
| 24 | `DatPorizeni_master` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Garanti_ZaznamyProVypocetOdmen_Log` (CLUSTERED) — `ID_master`
