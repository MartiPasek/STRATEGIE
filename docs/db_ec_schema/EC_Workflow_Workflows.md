# EC_Workflow_Workflows

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(255) | NE |  |  |
| 3 | `Popis` | nvarchar(500) | ANO |  |  |
| 4 | `MaxPokusu` | int | NE | ((3)) |  |
| 5 | `Aktivni` | bit | NE | ((1)) |  |
| 6 | `DatumVytvoreni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK__EC_Workf__3214EC07C86DF7EE` (CLUSTERED) — `Id`
