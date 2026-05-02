# EC_Workflow_Triggery

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 8 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(255) | NE |  |  |
| 3 | `Typ` | nvarchar(50) | NE |  |  |
| 4 | `IdKonektor` | int | ANO |  |  |
| 5 | `Pravidlo` | nvarchar(MAX) | ANO |  |  |
| 6 | `Aktivni` | bit | NE | ((1)) |  |
| 7 | `DatumVytvoreni` | datetime | NE | (getdate()) |  |
| 8 | `PosledniAktivita` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IdKonektor` → [`EC_Workflow_Konektory`](EC_Workflow_Konektory.md).`Id` _(constraint: `FK_Workflow_Triggery_Konektor`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC07113A33D5` (CLUSTERED) — `Id`
