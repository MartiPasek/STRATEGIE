# EC_Dochazka_NastavZar

**Schema**: dbo · **Cluster**: HR · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 29 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Firma` | nvarchar(64) | ANO |  |  |
| 3 | `RychlyLoginCas` | int | ANO |  |  |
| 4 | `TlObed` | bit | ANO | ((0)) |  |
| 5 | `TlSvacina` | bit | ANO | ((0)) |  |
| 6 | `TlKoureni` | bit | ANO | ((0)) |  |
| 7 | `TlOdchodNa` | bit | ANO | ((0)) |  |
| 8 | `TlDovolena` | bit | ANO | ((0)) |  |
| 9 | `TlOdvozy` | bit | ANO | ((0)) |  |
| 10 | `AutoLogoutCas` | int | ANO |  |  |
| 11 | `NacitejPoslPoznamku` | bit | ANO | ((0)) |  |
| 12 | `ZobrazujSeznam` | bit | ANO | ((0)) |  |
| 13 | `ZakazujLogin` | bit | ANO | ((0)) |  |
| 14 | `ManualZobrazKlav` | bit | ANO | ((0)) |  |
| 15 | `ZobrazeniKoef` | decimal(9,5) | ANO |  |  |
| 16 | `SeznamLidiRadky` | tinyint | ANO |  |  |
| 17 | `SeznamLidiSloupce` | tinyint | ANO |  |  |
| 18 | `PoslZakazkyPocet` | smallint | ANO | ((0)) |  |
| 19 | `CinnostiSloupce` | smallint | ANO |  |  |
| 20 | `CinnostiRadky` | smallint | ANO |  |  |
| 21 | `RezieSloupce` | smallint | ANO |  |  |
| 22 | `RezieRadky` | smallint | ANO |  |  |
| 23 | `MacAdress` | nvarchar(64) | ANO |  |  |
| 24 | `TypZarizeni` | tinyint | ANO |  |  |
| 25 | `LogLevel` | bit | ANO | ((0)) |  |
| 26 | `LogOnline` | bit | ANO | ((0)) |  |
| 27 | `Nazev` | nvarchar(255) | ANO |  |  |
| 28 | `MQTTtopic` | nvarchar(255) | ANO |  |  |
| 29 | `TlBeistellung` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_Dochazka_NastavZar` (CLUSTERED) — `ID`
