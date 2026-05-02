# EC_Workflow_StepPiny

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 5 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 1 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdKrokuFlow` | int | NE |  |  |
| 3 | `Nazev` | nvarchar(100) | NE |  |  |
| 4 | `TypDat` | nvarchar(50) | NE |  |  |
| 5 | `Schema` | nvarchar(MAX) | ANO |  |  |
| 6 | `ExtractPath` | nvarchar(500) | ANO |  |  |
| 7 | `Poradi` | int | NE | ((0)) |  |
| 8 | `Zdroj` | nvarchar(20) | NE | ('manual') |  |

## Cizí klíče (declared)

- `IdKrokuFlow` → [`EC_Workflow_KrokyFlow`](EC_Workflow_KrokyFlow.md).`Id` _(constraint: `FK_Workflow_StepPiny_Krok`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC07E386BF73` (CLUSTERED) — `Id`
- **UNIQUE** `UQ_Workflow_StepPiny_NazevKrok` (NONCLUSTERED) — `IdKrokuFlow, Nazev`
