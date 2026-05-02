# EC_Workflow_Propojeni

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 11 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 3 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdWorkflow` | int | NE |  |  |
| 3 | `IdCilovyKrok` | int | NE |  |  |
| 4 | `CilovyPin` | nvarchar(100) | NE |  |  |
| 5 | `Rezim` | nvarchar(5) | NE |  |  |
| 6 | `Hodnota` | nvarchar(MAX) | ANO |  |  |
| 7 | `IdZdrojovyKrok` | int | ANO |  |  |
| 8 | `ZdrojovyPin` | nvarchar(100) | ANO |  |  |
| 9 | `ZdrojovaCesta` | nvarchar(500) | ANO |  |  |

## Cizí klíče (declared)

- `IdWorkflow` → [`EC_Workflow_Workflows`](EC_Workflow_Workflows.md).`Id` _(constraint: `FK_Workflow_Propojeni_Workflow`)_
- `IdCilovyKrok` → [`EC_Workflow_KrokyFlow`](EC_Workflow_KrokyFlow.md).`Id` _(constraint: `FK_Workflow_Propojeni_CilovyKrok`)_
- `IdZdrojovyKrok` → [`EC_Workflow_KrokyFlow`](EC_Workflow_KrokyFlow.md).`Id` _(constraint: `FK_Workflow_Propojeni_ZdrojovyKrok`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC071C2015D6` (CLUSTERED) — `Id`
- **UNIQUE** `UQ_Workflow_Propojeni_CilovyPin` (NONCLUSTERED) — `IdWorkflow, IdCilovyKrok, CilovyPin`
