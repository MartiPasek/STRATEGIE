# EC_KontaktPLCGuru

**Schema**: dbo · **Cluster**: CRM · **Rows**: 486 · **Size**: 0.40 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `KontaktEmail` | nvarchar(50) | ANO |  |  |
| 3 | `LevelTestu` | nvarchar(50) | ANO |  |  |
| 4 | `DatPrijeti` | datetime | ANO |  |  |
| 5 | `CVPrilozeno` | bit | ANO |  |  |
| 6 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatZmeny` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_KontaktPLCGuru` (CLUSTERED) — `ID`
