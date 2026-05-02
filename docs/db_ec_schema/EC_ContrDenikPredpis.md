# EC_ContrDenikPredpis

**Schema**: dbo · **Cluster**: Other · **Rows**: 168 · **Size**: 0.13 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Blokovano` | bit | NE | ((0)) |  |
| 3 | `CisloZakazky` | nvarchar(50) | ANO |  |  |
| 4 | `CisloZam` | int | NE |  |  |
| 5 | `Castka` | numeric(18,2) | ANO |  |  |
| 6 | `Hodina` | numeric(18,2) | ANO |  |  |
| 7 | `Procento` | numeric(18,2) | ANO |  |  |
| 8 | `Smlouva` | nvarchar(5) | ANO |  |  |
| 9 | `Stredisko` | nvarchar(30) | ANO |  |  |
| 10 | `Typ` | int | ANO |  |  |
| 11 | `Typ_text` | varchar(24) | ANO |  |  |
| 12 | `IDContrUcet` | int | ANO |  |  |
| 13 | `PlatnostOd` | datetime | ANO |  |  |
| 14 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 18 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ContrDenikPredpis` (CLUSTERED) — `ID`
