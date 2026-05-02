# EC_Workflow_Fronta

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 7 · **Size**: 0.20 MB · **Sloupců**: 18 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdWorkflow` | int | NE |  |  |
| 3 | `IdFlowVerze` | int | NE |  |  |
| 4 | `FileHash` | nvarchar(64) | ANO |  |  |
| 5 | `NazevSouboru` | nvarchar(500) | ANO |  |  |
| 6 | `CestaSouboru` | nvarchar(1000) | ANO |  |  |
| 7 | `MimeType` | nvarchar(100) | ANO |  |  |
| 8 | `Stav` | nvarchar(50) | NE | ('queued') |  |
| 9 | `RetryPocet` | int | NE | ((0)) |  |
| 10 | `RetryDalsiPokus` | datetime | ANO |  |  |
| 11 | `IdRodicFronty` | int | ANO |  |  |
| 12 | `RodicPoradi` | int | ANO |  |  |
| 13 | `PuvodniAiVysledek` | nvarchar(MAX) | ANO |  |  |
| 14 | `FinalniVysledek` | nvarchar(MAX) | ANO |  |  |
| 15 | `SchvalilUzivatel` | nvarchar(255) | ANO |  |  |
| 16 | `DatumSchvaleni` | datetime | ANO |  |  |
| 17 | `DatumVlozeni` | datetime | NE | (getdate()) |  |
| 18 | `DatumZpracovani` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IdWorkflow` → [`EC_Workflow_Workflows`](EC_Workflow_Workflows.md).`Id` _(constraint: `FK_Workflow_Fronta_Workflow`)_
- `IdFlowVerze` → [`EC_Workflow_FlowVerze`](EC_Workflow_FlowVerze.md).`Id` _(constraint: `FK_Workflow_Fronta_FlowVerze`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC07DDA18EC8` (CLUSTERED) — `Id`
