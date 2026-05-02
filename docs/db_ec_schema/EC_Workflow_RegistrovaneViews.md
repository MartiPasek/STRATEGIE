# EC_Workflow_RegistrovaneViews

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdKonektor` | int | ANO |  |  |
| 3 | `NazevView` | nvarchar(255) | NE |  |  |
| 4 | `Popis` | nvarchar(500) | ANO |  |  |
| 5 | `Aktivni` | bit | NE | ((1)) |  |

## Indexy

- **PK** `PK__EC_Workf__3214EC07DD7DBE83` (CLUSTERED) — `Id`
- **UNIQUE** `UQ_Workflow_RegistrovaneViews_Nazev` (NONCLUSTERED) — `NazevView`
