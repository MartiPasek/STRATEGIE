# EC_Workflow_FlowVerze

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdWorkflow` | int | NE |  |  |
| 3 | `Verze` | int | NE |  |  |
| 4 | `Konfigurace` | nvarchar(MAX) | NE |  |  |
| 5 | `DatumVytvoreni` | datetime | NE | (getdate()) |  |
| 6 | `Aktivni` | bit | NE | ((0)) |  |

## Cizí klíče (declared)

- `IdWorkflow` → [`EC_Workflow_Workflows`](EC_Workflow_Workflows.md).`Id` _(constraint: `FK_Workflow_FlowVerze_Workflow`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC07E9A6AE41` (CLUSTERED) — `Id`
