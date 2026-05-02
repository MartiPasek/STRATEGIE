# EC_Personalistika_DuvodZamitnuti

**Schema**: dbo · **Cluster**: HR · **Rows**: 15 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | int | ANO |  |  |
| 3 | `Popis` | nvarchar(250) | ANO |  |  |
| 4 | `Poznamka` | nvarchar(2000) | ANO |  |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Personalistika_DuvodZamitnuti` (CLUSTERED) — `ID`
