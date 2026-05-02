# EC_Workflow_TypyKonektoru

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 14 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 1 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Kod` | nvarchar(50) | NE |  |  |
| 3 | `TypDriveru` | nvarchar(50) | NE |  |  |
| 4 | `Nazev` | nvarchar(100) | NE |  |  |
| 5 | `Popis` | nvarchar(500) | ANO |  |  |
| 6 | `ContraktSchema` | nvarchar(MAX) | ANO |  |  |
| 7 | `StepType` | nvarchar(50) | ANO |  |  |
| 8 | `Aktivni` | bit | NE | ((1)) |  |
| 9 | `DatumVytvoreni` | datetime | NE | (getdate()) |  |

## Cizí klíče (declared)

- `TypDriveru` → [`EC_Workflow_TypyDriveru`](EC_Workflow_TypyDriveru.md).`Kod` _(constraint: `FK_Workflow_TypyKonektoru_Driver`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC0782785A13` (CLUSTERED) — `Id`
- **UNIQUE** `UQ_Workflow_TypyKonektoru_Kod` (NONCLUSTERED) — `Kod`
