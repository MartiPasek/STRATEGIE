# EC_CaroveKody

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 172,703 · **Size**: 16.20 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `CisloOrg` | int | ANO |  |  |
| 3 | `ObjCis` | nvarchar(50) | ANO |  |  |
| 5 | `BARCODE` | nvarchar(50) | ANO |  |  |
| 6 | `ProductEAN` | nvarchar(50) | ANO |  |  |
| 7 | `Mnozstvi` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_CaroveKody` (CLUSTERED) — `id`
