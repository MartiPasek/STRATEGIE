# EC_Odpisy

**Schema**: dbo · **Cluster**: Other · **Rows**: 10 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Rok` | int | ANO |  |  |
| 3 | `IDDoklad` | int | ANO |  |  |
| 4 | `KcCelkemBezDPH` | numeric(18,2) | ANO |  |  |
| 5 | `Stredisko` | nvarchar(10) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(500) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Odpisy` (CLUSTERED) — `ID`
