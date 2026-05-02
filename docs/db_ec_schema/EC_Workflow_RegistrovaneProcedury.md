# EC_Workflow_RegistrovaneProcedury

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 5 · **FK**: 1 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdKonektor` | int | ANO |  |  |
| 3 | `NazevProcedury` | nvarchar(255) | NE |  |  |
| 4 | `Popis` | nvarchar(500) | ANO |  |  |
| 5 | `Aktivni` | bit | NE | ((1)) |  |

## Cizí klíče (declared)

- `IdKonektor` → [`EC_Workflow_Konektory`](EC_Workflow_Konektory.md).`Id` _(constraint: `FK_Workflow_RegistrovaneProcedury_Konektor`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC074062CABD` (CLUSTERED) — `Id`
- **UNIQUE** `UQ_Workflow_RegistrovaneProcedury_Nazev` (NONCLUSTERED) — `NazevProcedury`
