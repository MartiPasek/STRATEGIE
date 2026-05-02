# EC_Sklad_VydejResitTemp

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 29 · **FK**: 0 · **Indexů**: 1

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
| 13 | `Umisteni_KOD` | nvarchar(15) | ANO | ('') |  |
| 14 | `nezobrazuj` | bit | ANO | ((0)) |  |
| 15 | `IDKmenZbo` | int | ANO |  |  |
| 16 | `PoznamkaNakup` | nvarchar(128) | ANO |  |  |
| 17 | `ID_Vydejky` | int | ANO |  |  |
| 18 | `ID_PolVydejky` | int | ANO |  |  |
| 19 | `Nalezeno` | numeric(19,6) | ANO |  |  |
| 20 | `Priorita` | int | ANO |  |  |
| 21 | `Resil` | nvarchar(128) | ANO |  |  |
| 22 | `DatReseni` | datetime | ANO |  |  |
| 23 | `Reseno` | bit | ANO |  |  |
| 24 | `JeVKM` | bit | ANO | ((0)) |  |
| 25 | `Predano` | bit | ANO | ((0)) |  |
| 26 | `Predal` | nvarchar(128) | ANO |  |  |
| 27 | `DatPredani` | datetime | ANO |  |  |
| 28 | `Zpracovano` | bit | ANO | ((0)) |  |
| 29 | `Smazano` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_Sklad_VydejResitTemp` (CLUSTERED) — `ID`
