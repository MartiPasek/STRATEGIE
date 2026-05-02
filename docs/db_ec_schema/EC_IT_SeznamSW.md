# EC_IT_SeznamSW

**Schema**: dbo · **Cluster**: Other · **Rows**: 23 · **Size**: 0.20 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Id_PC` | int | ANO |  |  |
| 3 | `Id_Typ` | nvarchar(30) | ANO |  |  |
| 4 | `Id_Vyrobce` | nvarchar(30) | ANO |  |  |
| 5 | `Model` | nvarchar(30) | ANO |  |  |
| 6 | `Verze` | nvarchar(30) | ANO |  |  |
| 7 | `Licencni_Klic` | nvarchar(50) | ANO |  |  |
| 8 | `Platnost_Do` | datetime | ANO |  |  |
| 9 | `Popis` | nvarchar(150) | ANO |  |  |
| 10 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_IT_SeznamSW` (CLUSTERED) — `Id`
