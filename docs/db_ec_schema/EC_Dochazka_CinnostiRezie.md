# EC_Dochazka_CinnostiRezie

**Schema**: dbo · **Cluster**: HR · **Rows**: 32 · **Size**: 0.07 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Cislo` | int | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `ZobrazujVDochazce` | bit | NE | ((0)) |  |
| 7 | `CisloOldDochazka` | int | ANO |  |  |
| 8 | `DogenerovatDoch` | bit | ANO |  |  |
| 9 | `ZobrazujVOdchodNa` | bit | ANO |  |  |
| 10 | `MaxDobaMin` | int | ANO |  |  |
| 11 | `DogenerovatCasMin` | int | ANO |  |  |
| 12 | `JePrestavka` | bit | ANO |  |  |
| 13 | `Zakazka` | nvarchar(10) | ANO |  |  |
| 14 | `NepocitatDoMezd` | bit | ANO |  |  |
| 15 | `NevracetNaCinnost` | bit | ANO | ((0)) |  |
| 16 | `NekontrolovatPrekryv` | bit | ANO |  |  |
| 17 | `JeVolno` | bit | ANO | ((0)) |  |
| 18 | `Blokovano` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_Dochazka_CinnostiRezie` (CLUSTERED) — `ID`
