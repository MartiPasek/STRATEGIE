# EC_EventLog

**Schema**: dbo · **Cluster**: Logging · **Rows**: 10,581 · **Size**: 2.44 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDEvent` | int | ANO |  |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `Poznamka` | nvarchar(500) | ANO |  |  |

## Indexy

- **PK** `PK_EC_EventLog` (CLUSTERED) — `ID`
