# EC_DELPHI_Diagnostika

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 0 · **Size**: 0.16 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `bugreport` | nvarchar(MAX) | NE |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Delphi_Diagnostika` (CLUSTERED) — `ID`
