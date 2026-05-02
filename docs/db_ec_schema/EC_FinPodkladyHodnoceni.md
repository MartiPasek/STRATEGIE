# EC_FinPodkladyHodnoceni

**Schema**: dbo · **Cluster**: Finance · **Rows**: 7 · **Size**: 0.07 MB · **Sloupců**: 26 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Mesic` | int | ANO |  |  |
| 4 | `Rok` | int | ANO |  |  |
| 5 | `PocetHodin` | numeric(18,2) | ANO |  |  |
| 6 | `ZakladRezie` | numeric(18,0) | ANO |  |  |
| 7 | `OsOhod` | numeric(18,0) | ANO |  |  |
| 8 | `IndividualOhod` | numeric(18,0) | ANO |  |  |
| 9 | `MzdaCelkem` | numeric(26,0) | ANO |  |  |
| 10 | `DovolenaNarokD` | numeric(18,0) | ANO |  |  |
| 11 | `DovolenaCerpD` | numeric(18,0) | ANO |  |  |
| 12 | `DovolenaZustD` | numeric(19,0) | ANO |  |  |
| 13 | `DovolenaKc` | numeric(18,0) | ANO |  |  |
| 14 | `PlaceneVolKc` | numeric(18,0) | ANO |  |  |
| 15 | `DovolenaHod` | numeric(18,0) | ANO |  |  |
| 16 | `Premie1` | numeric(18,0) | ANO |  |  |
| 17 | `Premie2` | numeric(18,0) | ANO |  |  |
| 18 | `Premie` | numeric(18,0) | ANO |  |  |
| 19 | `VykonovaPremie` | numeric(18,0) | ANO |  |  |
| 20 | `StravenkyKc` | numeric(18,0) | ANO |  |  |
| 21 | `NaUcet` | numeric(18,0) | ANO |  |  |
| 22 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 23 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 24 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 25 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 26 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_FinPodkladyProMzdy` (CLUSTERED) — `ID`
