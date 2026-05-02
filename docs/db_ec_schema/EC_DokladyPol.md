# EC_DokladyPol

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 45 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDZboSklad` | int | ANO |  |  |
| 3 | `IDDoklad` | int | NE |  |  |
| 4 | `IDOldDoklad` | int | ANO |  |  |
| 5 | `Poradi` | int | ANO |  |  |
| 6 | `SkupZbo` | nvarchar(3) | NE | ('') |  |
| 7 | `RegCis` | nvarchar(30) | NE | ('') |  |
| 8 | `Nazev1` | nvarchar(100) | NE | ('') |  |
| 9 | `Nazev2` | nvarchar(100) | NE | ('') |  |
| 10 | `Nazev3` | nvarchar(100) | NE | ('') |  |
| 11 | `Nazev4` | nvarchar(100) | NE | ('') |  |
| 12 | `SKP` | nvarchar(50) | ANO | ('') |  |
| 13 | `Popis4` | nvarchar(100) | NE | ('') |  |
| 14 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 15 | `CisloZam` | int | ANO |  |  |
| 16 | `MJ` | nvarchar(10) | ANO |  |  |
| 17 | `Mena` | nvarchar(3) | ANO |  |  |
| 18 | `Kurz` | numeric(19,6) | NE | ((1.0)) |  |
| 19 | `KurzEuro` | numeric(19,6) | NE | ((0)) |  |
| 20 | `SazbaDPH` | numeric(5,2) | ANO |  |  |
| 21 | `Mnozstvi` | numeric(19,6) | NE | ((0.0)) |  |
| 22 | `MnOdebrane` | numeric(19,6) | NE | ((0.0)) |  |
| 23 | `MnozstviStorno` | numeric(19,6) | NE | ((0.0)) |  |
| 24 | `VstupniCena` | tinyint | NE | ((0)) |  |
| 25 | `JCbezDaniKC` | numeric(19,6) | NE | ((0.0)) |  |
| 26 | `JCbezDaniVal` | numeric(19,6) | NE | ((0.0)) |  |
| 27 | `CCbezDaniKc` | numeric(19,6) | NE | ((0.0)) |  |
| 28 | `CCbezDaniVal` | numeric(19,6) | NE | ((0.0)) |  |
| 29 | `Poznamka` | ntext | ANO |  |  |
| 30 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 31 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 32 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 33 | `DatZmeny` | datetime | ANO |  |  |
| 34 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 35 | `IDOldPolozka` | int | ANO |  |  |
| 36 | `CisloOrg` | int | ANO |  |  |
| 37 | `DruhPohybuZbo` | tinyint | NE |  |  |
| 38 | `PotvrzDatDod` | datetime | ANO |  |  |
| 39 | `PozadDatDod` | datetime | ANO |  |  |
| 40 | `Hmotnost` | numeric(19,6) | NE | ((0.0)) |  |
| 41 | `StredNaklad` | nvarchar(30) | ANO |  |  |
| 42 | `HmotnostBrutto` | numeric(19,6) | NE | ((0.0)) |  |
| 43 | `BarCode` | nvarchar(50) | ANO |  |  |
| 44 | `IdUmisteni` | int | ANO |  |  |
| 45 | `Prevedeno` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_DokladyPol` (CLUSTERED) — `ID`
