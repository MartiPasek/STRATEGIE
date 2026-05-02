# EC_ZakazkySW

**Schema**: dbo · **Cluster**: Finance · **Rows**: 654 · **Size**: 0.39 MB · **Sloupců**: 36 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Zakaznik` | nvarchar(200) | ANO |  |  |
| 3 | `SazbaVal` | numeric(18,2) | ANO |  |  |
| 4 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 5 | `CisloOrg` | int | ANO |  |  |
| 6 | `NakladyCelkemVal` | numeric(18,2) | NE | ((0)) |  |
| 7 | `NakladyCelkemKc` | numeric(19,6) | NE | ((0)) |  |
| 8 | `Kurz` | numeric(9,5) | NE | ((1)) |  |
| 9 | `Mena` | nvarchar(10) | NE | (N'CZK') |  |
| 10 | `Stredisko` | nvarchar(30) | ANO |  |  |
| 11 | `DietyPocetDni` | numeric(19,6) | NE | ((0)) |  |
| 12 | `DietySazba` | numeric(19,6) | NE | ((0)) |  |
| 13 | `DietyKc` | numeric(38,6) | ANO |  |  |
| 14 | `DietyVal` | numeric(38,11) | ANO |  |  |
| 15 | `PraceHod` | numeric(18,2) | NE | ((0)) |  |
| 16 | `PraceKc` | numeric(19,6) | NE | ((0)) |  |
| 17 | `PraceVal` | numeric(19,6) | NE | ((0)) |  |
| 18 | `OstatniNakladVal` | numeric(18,2) | NE | ((0)) |  |
| 19 | `OstatniNakladKc` | numeric(19,6) | NE | ((0)) |  |
| 20 | `CestCasKc` | numeric(19,6) | NE | ((0)) |  |
| 21 | `CestCasVal` | numeric(19,6) | NE | ((0)) |  |
| 22 | `CestCasHod` | numeric(19,6) | NE | ((0)) |  |
| 23 | `KilometryKc` | numeric(19,6) | NE | ((0)) |  |
| 24 | `KilometryVal` | numeric(19,6) | NE | ((0)) |  |
| 25 | `PocetKm` | numeric(18,2) | NE | ((0)) |  |
| 26 | `UbytovaniKc` | numeric(19,6) | NE | ((0)) |  |
| 27 | `UbytovaniVal` | numeric(19,6) | NE | ((0)) |  |
| 28 | `NakladyCelkemOstVal` | numeric(19,6) | ANO |  |  |
| 29 | `NakladyCelkemOstKc` | numeric(19,6) | ANO |  |  |
| 30 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 31 | `CisloZam` | int | ANO |  |  |
| 32 | `FakturovanoNaZakaznika` | numeric(19,6) | ANO |  |  |
| 33 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 34 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 35 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 36 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ZakazkySW` (CLUSTERED) — `ID`
