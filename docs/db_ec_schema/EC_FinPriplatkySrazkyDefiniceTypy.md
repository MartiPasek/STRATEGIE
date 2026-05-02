# EC_FinPriplatkySrazkyDefiniceTypy

**Schema**: dbo · **Cluster**: Finance · **Rows**: 49 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Opravneni` | int | NE | ((1)) |  |
| 3 | `Nazev` | nvarchar(70) | ANO |  |  |
| 4 | `ReakceMzdy` | bit | NE | ((0)) |  |
| 5 | `Aktivni` | bit | NE | ((0)) |  |
| 6 | `ZobrazujVeVyplatnici` | bit | NE | ((0)) |  |
| 7 | `MzdovaSlozka` | int | ANO |  |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 12 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_FinPriplatkySrazkyDefiniceTypy` (CLUSTERED) — `ID`
