# EC_ContrKontaD

**Schema**: dbo · **Cluster**: Other · **Rows**: 220 · **Size**: 0.20 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Sum` | nchar(1) | NE |  |  |
| 3 | `Stredisko` | nvarchar(20) | ANO |  |  |
| 4 | `IDContrUcet` | int | ANO |  |  |
| 5 | `Castka` | numeric(18,2) | ANO |  |  |
| 6 | `Rok` | int | ANO |  |  |
| 7 | `Mesic` | int | ANO |  |  |
| 8 | `Tyden` | int | ANO |  |  |
| 9 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 10 | `Pocet` | int | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 14 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ContrKontaD` (CLUSTERED) — `ID`
