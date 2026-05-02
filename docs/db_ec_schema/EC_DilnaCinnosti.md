# EC_DilnaCinnosti

**Schema**: dbo · **Cluster**: Other · **Rows**: 45 · **Size**: 0.07 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 5 | `Cislo` | int | ANO |  |  |
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
| 19 | `NepocitatDoPritomnychBudova` | bit | ANO |  |  |
| 20 | `NepocitatDoHodnoceni` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_DilnaCinnosti` (CLUSTERED) — `ID`
