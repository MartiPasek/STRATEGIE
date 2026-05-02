# EC_Dochazka_PlanNepritomnost

**Schema**: dbo · **Cluster**: HR · **Rows**: 20,519 · **Size**: 3.07 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumPripadu` | datetime | ANO |  |  |
| 3 | `DenVTydnu` | nvarchar(2) | ANO |  |  |
| 4 | `DruhCinnosti` | smallint | ANO |  |  |
| 5 | `Jmeno` | nvarchar(100) | ANO |  |  |
| 6 | `Prijmeni` | nvarchar(100) | ANO |  |  |
| 7 | `LoginId` | nvarchar(128) | ANO |  |  |
| 8 | `CisloZam` | int | ANO |  |  |
| 9 | `Nazev` | nvarchar(100) | ANO |  |  |
| 10 | `PocetHodin` | int | ANO |  |  |
| 11 | `Zmenil` | nchar(20) | ANO |  |  |
| 12 | `DatPorizeni` | datetime | ANO |  |  |
| 13 | `Autor` | nvarchar(50) | ANO |  |  |
| 14 | `Barva` | nvarchar(10) | ANO |  |  |
| 15 | `GenerovanoZDochazky` | bit | ANO | ((0)) |  |
| 16 | `Schvaleno` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_Dochazka_PlanNepritomnost` (CLUSTERED) — `ID`
