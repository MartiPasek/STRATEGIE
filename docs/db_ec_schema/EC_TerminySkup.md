# EC_TerminySkup

**Schema**: dbo · **Cluster**: Other · **Rows**: 12 · **Size**: 0.07 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Skupina` | int | NE |  |  |
| 3 | `Popis` | nchar(40) | NE |  |  |
| 4 | `Poznamka` | nchar(100) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `DatPorizeni_D` | int | ANO |  |  |
| 10 | `DatPorizeni_M` | int | ANO |  |  |
| 11 | `DatPorizeni_Y` | int | ANO |  |  |
| 12 | `DatPorizeni_Q` | int | ANO |  |  |
| 13 | `DatPorizeni_W` | int | ANO |  |  |
| 14 | `DatPorizeni_X` | datetime | ANO |  |  |
| 15 | `DatZmeny_D` | int | ANO |  |  |
| 16 | `DatZmeny_M` | int | ANO |  |  |
| 17 | `DatZmeny_Y` | int | ANO |  |  |
| 18 | `DatZmeny_Q` | int | ANO |  |  |
| 19 | `DatZmeny_W` | int | ANO |  |  |
| 20 | `DatZmeny_X` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_TerminySkup` (CLUSTERED) — `ID`
- **UNIQUE** `UQ__Skupina` (NONCLUSTERED) — `Skupina`
