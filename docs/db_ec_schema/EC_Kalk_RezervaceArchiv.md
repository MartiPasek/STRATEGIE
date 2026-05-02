# EC_Kalk_RezervaceArchiv

**Schema**: dbo · **Cluster**: Production · **Rows**: 138 · **Size**: 0.14 MB · **Sloupců**: 23 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Autor` | nvarchar(128) | ANO |  |  |
| 2 | `Vydej` | numeric(18,2) | ANO |  |  |
| 3 | `objednej` | numeric(18,2) | ANO |  |  |
| 4 | `ZakazkaKalkulace` | nvarchar(15) | ANO |  |  |
| 5 | `Presunout` | int | NE |  |  |
| 6 | `ID` | int | ANO |  |  |
| 7 | `IDObj` | int | ANO |  |  |
| 8 | `IDKmenZbozi` | int | ANO |  |  |
| 9 | `PoradoveCislo` | int | ANO |  |  |
| 10 | `dodavatel` | nvarchar(255) | ANO |  |  |
| 11 | `RegCis` | nvarchar(30) | ANO |  |  |
| 12 | `nazev1` | nvarchar(100) | ANO |  |  |
| 13 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 14 | `MnozstviObj` | numeric(19,6) | ANO |  |  |
| 15 | `MnozstviObjZbyva` | numeric(19,6) | ANO |  |  |
| 16 | `MnOdebrane` | numeric(19,6) | ANO |  |  |
| 17 | `IdPolKalk` | int | NE |  |  |
| 18 | `MnozstviKalkulace` | numeric(19,2) | ANO |  |  |
| 19 | `Kalkulovano` | numeric(38,2) | ANO |  |  |
| 20 | `CisloZakazkyZdroj` | nvarchar(100) | ANO |  |  |
| 21 | `PoznamkaNakup` | nvarchar(128) | ANO |  |  |
| 22 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 23 | `IDPresunu` | int | ANO |  |  |
