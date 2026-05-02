# EC_GarantiParametryOdmen

**Schema**: dbo · **Cluster**: Finance · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(200) | ANO |  |  |
| 3 | `Castka` | numeric(18,4) | ANO |  |  |
| 4 | `Autor` | nvarchar(50) | NE | (suser_name()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(50) | ANO |  |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK__EC_Garan__3214EC272C6D7D62` (CLUSTERED) — `ID`
