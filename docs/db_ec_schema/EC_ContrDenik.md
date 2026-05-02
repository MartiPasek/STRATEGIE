# EC_ContrDenik

**Schema**: dbo · **Cluster**: Other · **Rows**: 6,428 · **Size**: 1.38 MB · **Sloupců**: 26 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DUD` | int | NE |  |  |
| 3 | `IDContrUcet` | int | ANO |  |  |
| 4 | `IDDenik` | int | ANO |  |  |
| 5 | `IDPohybyZbo` | int | ANO |  |  |
| 6 | `CisloRadek` | int | ANO |  |  |
| 7 | `CisloDoklad` | int | ANO |  |  |
| 8 | `CisloUctUcet` | nvarchar(30) | ANO |  |  |
| 9 | `NazevUctu` | nvarchar(220) | ANO |  |  |
| 10 | `Mena` | nvarchar(50) | ANO |  |  |
| 11 | `Kurz` | numeric(18,2) | ANO |  |  |
| 12 | `DatumPripad` | datetime | ANO |  |  |
| 13 | `CisloOrg` | int | ANO |  |  |
| 14 | `CisloZam` | int | ANO |  |  |
| 15 | `Castka` | numeric(18,2) | ANO |  |  |
| 16 | `Utvar` | int | ANO |  |  |
| 17 | `CisloZakazky` | nvarchar(20) | ANO |  |  |
| 18 | `Popis` | nvarchar(200) | ANO |  |  |
| 19 | `Mesic` | int | ANO |  |  |
| 20 | `Rok` | int | ANO |  |  |
| 21 | `Tyden` | int | ANO |  |  |
| 22 | `FinPlan` | bit | ANO | ((0)) |  |
| 23 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 24 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 25 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 26 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_TabDenikC` (CLUSTERED) — `ID`
