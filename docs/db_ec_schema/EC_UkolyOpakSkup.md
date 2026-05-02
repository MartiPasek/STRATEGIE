# EC_UkolyOpakSkup

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Skupina` | int | NE |  |  |
| 3 | `Popis` | nchar(40) | NE |  |  |
| 4 | `Poznamka` | nchar(100) | ANO |  |  |
| 22 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 23 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 24 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 25 | `DatZmeny` | datetime | ANO |  |  |
| 26 | `DatPorizeni_D` | int | ANO |  |  |
| 27 | `DatPorizeni_M` | int | ANO |  |  |
| 28 | `DatPorizeni_Y` | int | ANO |  |  |
| 29 | `DatPorizeni_Q` | int | ANO |  |  |
| 30 | `DatPorizeni_W` | int | ANO |  |  |
| 31 | `DatPorizeni_X` | datetime | ANO |  |  |
| 32 | `DatZmeny_D` | int | ANO |  |  |
| 33 | `DatZmeny_M` | int | ANO |  |  |
| 34 | `DatZmeny_Y` | int | ANO |  |  |
| 35 | `DatZmeny_Q` | int | ANO |  |  |
| 36 | `DatZmeny_W` | int | ANO |  |  |
| 37 | `DatZmeny_X` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_UkolyOpakSkup` (CLUSTERED) — `ID`
- **UNIQUE** `UQ__EC_Ukoly__0F10E22805F842C2` (NONCLUSTERED) — `Skupina`
