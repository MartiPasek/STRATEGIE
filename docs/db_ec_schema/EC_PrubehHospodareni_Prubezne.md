# EC_PrubehHospodareni_Prubezne

**Schema**: dbo · **Cluster**: Finance · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Rok` | int | ANO |  |  |
| 3 | `Stredisko` | nvarchar(10) | ANO |  |  |
| 4 | `KalkHodiny` | numeric(18,2) | ANO |  |  |
| 5 | `RealHodiny` | numeric(18,2) | ANO |  |  |
| 6 | `Naklady` | numeric(18,2) | ANO |  |  |
| 7 | `Vynosy` | numeric(18,2) | ANO |  |  |
| 8 | `Zisk` | numeric(18,2) | ANO |  |  |
| 9 | `RezieCelkem` | numeric(18,2) | ANO |  |  |
| 10 | `PrumMzdaDilna` | numeric(18,2) | ANO |  |  |
| 11 | `RezieNaKalkHod` | numeric(18,2) | ANO |  |  |
| 12 | `DatPoslAktualizace` | datetime | ANO |  |  |
| 13 | `AutorAktualizace` | nvarchar(125) | ANO |  |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_PrubehHospodareni_Prubezne` (CLUSTERED) — `ID`
