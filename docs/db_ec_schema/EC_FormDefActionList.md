# EC_FormDefActionList

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 78 · **Size**: 0.11 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloAkce` | int | NE |  |  |
| 3 | `NazevAkce` | nvarchar(50) | ANO |  |  |
| 4 | `Parametr` | nvarchar(50) | ANO |  |  |
| 5 | `Popis` | ntext | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_FormDefActionList` (CLUSTERED) — `ID`
