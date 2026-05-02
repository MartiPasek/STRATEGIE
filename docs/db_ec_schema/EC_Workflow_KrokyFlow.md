# EC_Workflow_KrokyFlow

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdWorkflow` | int | NE |  |  |
| 3 | `Poradi` | int | NE |  |  |
| 4 | `TypKroku` | nvarchar(50) | NE |  |  |
| 5 | `Nazev` | nvarchar(255) | ANO |  |  |
| 6 | `IdKonektoru` | int | ANO |  |  |
| 7 | `RetryPolicy` | nvarchar(MAX) | ANO |  |  |

## Cizí klíče (declared)

- `IdWorkflow` → [`EC_Workflow_Workflows`](EC_Workflow_Workflows.md).`Id` _(constraint: `FK_Workflow_KrokyFlow_Workflow`)_
- `IdKonektoru` → [`EC_Workflow_Konektory`](EC_Workflow_Konektory.md).`Id` _(constraint: `FK_Workflow_KrokyFlow_Konektor`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC0706F028B6` (CLUSTERED) — `Id`
