# EC_Rezervace_Archiv

**Schema**: dbo · **Cluster**: Other · **Rows**: 43,471 · **Size**: 19.95 MB · **Sloupců**: 23 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Autor` | nvarchar(128) | ANO |  |  |
| 2 | `Vydej` | numeric(18,2) | ANO |  |  |
| 3 | `objednej` | numeric(18,2) | ANO |  |  |
| 4 | `ZakazkaKalkulace` | nvarchar(100) | ANO |  |  |
| 5 | `Presunout` | int | ANO |  |  |
| 6 | `ID` | int | NE |  |  |
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
| 17 | `IdPolKalk` | int | ANO |  |  |
| 18 | `MnozstviKalkulace` | numeric(19,2) | ANO |  |  |
| 19 | `Kalkulovano` | numeric(38,2) | ANO |  |  |
| 20 | `CisloZakazkyZdroj` | nvarchar(100) | ANO |  |  |
| 21 | `PoznamkaNakup` | nvarchar(128) | ANO |  |  |
| 22 | `Objednano` | numeric(18,2) | ANO |  |  |
| 23 | `Vydano` | numeric(18,2) | ANO |  |  |
