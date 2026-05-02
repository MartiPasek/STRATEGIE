# EC_Sklad_VydejTemp_LogDEL

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 0

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
| 11 | `Umisteni_KOD` | nvarchar(100) | ANO |  |  |
| 12 | `nezobrazuj` | bit | ANO |  |  |
| 13 | `IDKmenZbo` | int | ANO |  |  |
| 14 | `PoznamkaNakup` | nvarchar(128) | ANO |  |  |
| 15 | `ID_Vydejky` | int | ANO |  |  |
| 16 | `ID_PolVydejky` | int | ANO |  |  |
| 17 | `AutorSmazani` | nvarchar(128) | ANO |  |  |
| 18 | `DatSmazani` | datetime | ANO |  |  |
| 19 | `Autor` | nvarchar(128) | ANO |  |  |
| 20 | `DatPorizeni` | datetime | ANO |  |  |
| 21 | `Smazano` | bit | ANO | ((0)) |  |
