# EC_Sklad_VydejPozadavkuTemp

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Poradi` | int | ANO |  |  |
| 3 | `RegCis` | nvarchar(30) | ANO |  |  |
| 4 | `Nazev1` | nvarchar(100) | ANO |  |  |
| 5 | `Poznamka` | ntext | ANO |  |  |
| 6 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 7 | `MnozstviPuvodni` | numeric(19,6) | ANO |  |  |
| 8 | `MnozstviOdebrane` | numeric(19,6) | ANO |  |  |
| 9 | `StavSkladu` | numeric(19,6) | ANO |  |  |
| 10 | `MJ` | nvarchar(10) | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 12 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 13 | `Umisteni_KOD` | nvarchar(100) | ANO | ('') |  |
| 14 | `nezobrazuj` | bit | ANO | ((0)) |  |
| 15 | `IDKmenZbo` | int | ANO |  |  |
| 16 | `PoznamkaNakup` | nvarchar(128) | ANO |  |  |
| 17 | `ID_Pozadavku` | int | ANO |  |  |
| 18 | `ID_PolPozadavku` | int | ANO |  |  |
| 19 | `Smazano` | bit | ANO | ((0)) |  |
| 20 | `ZustaloVeSkladu` | bit | ANO | ((0)) |  |
| 21 | `OsOdberSklad` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_Sklad_VydejPozadavkuTemp` (CLUSTERED) — `ID`
