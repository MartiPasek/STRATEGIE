# EC_Workflow_VysledkyKroku

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 25 · **Size**: 1.89 MB · **Sloupců**: 11 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdFronta` | int | NE |  |  |
| 3 | `Poradi` | int | NE |  |  |
| 4 | `TypKroku` | nvarchar(50) | NE |  |  |
| 5 | `Stav` | nvarchar(50) | NE |  |  |
| 6 | `Vstup` | nvarchar(MAX) | ANO |  |  |
| 7 | `Vystup` | nvarchar(MAX) | ANO |  |  |
| 8 | `ChybaDetail` | nvarchar(MAX) | ANO |  |  |
| 9 | `Confidence` | decimal(3,2) | ANO |  |  |
| 10 | `DatumZacatku` | datetime | ANO |  |  |
| 11 | `DatumKonce` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IdFronta` → [`EC_Workflow_Fronta`](EC_Workflow_Fronta.md).`Id` _(constraint: `FK_Workflow_VysledkyKroku_Fronta`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC07E8C4BA81` (CLUSTERED) — `Id`
