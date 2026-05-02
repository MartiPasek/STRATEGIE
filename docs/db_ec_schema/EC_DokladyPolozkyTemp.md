# EC_DokladyPolozkyTemp

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 315 · **Size**: 0.22 MB · **Sloupců**: 31 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_PolozkaPohyby` | int | ANO |  |  |
| 3 | `IDDoklad` | int | ANO |  |  |
| 4 | `Poradi` | int | ANO |  |  |
| 5 | `RegCis` | nvarchar(30) | ANO |  |  |
| 6 | `Nazev1` | nvarchar(100) | ANO |  |  |
| 7 | `Nazev2` | nvarchar(100) | ANO |  |  |
| 8 | `Poznamka` | ntext | ANO |  |  |
| 9 | `Mnozstvi` | numeric(19,6) | ANO | ((0.0)) |  |
| 10 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 11 | `MJ` | nvarchar(10) | ANO |  |  |
| 12 | `Mena` | nvarchar(3) | ANO |  |  |
| 13 | `Kurz` | numeric(19,6) | ANO | ((1.0)) |  |
| 14 | `SazbaDPH` | numeric(5,2) | ANO |  |  |
| 15 | `MnOdebrane` | numeric(19,6) | ANO | ((0.0)) |  |
| 16 | `VstupniCena` | tinyint | ANO | ((0)) |  |
| 17 | `JCbezDaniKC` | numeric(19,6) | ANO | ((0.0)) |  |
| 18 | `JCbezDaniVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 19 | `CCbezDaniKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 20 | `CCsDPHKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 21 | `CCbezDaniVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 22 | `CCsDPHVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 23 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 24 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 25 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 26 | `DatZmeny` | datetime | ANO |  |  |
| 27 | `IDOldPolozka` | int | ANO |  |  |
| 28 | `PotvrzDatDod` | datetime | ANO |  |  |
| 29 | `PozadDatDod` | datetime | ANO |  |  |
| 30 | `Hmotnost` | numeric(19,6) | ANO | ((0.0)) |  |
| 31 | `StredNaklad` | nvarchar(30) | ANO |  |  |

## Indexy

- **PK** `PK_EC_DokladyPolozkyTemp` (CLUSTERED) — `ID`
