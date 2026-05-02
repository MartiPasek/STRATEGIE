# EC_Sklad_Vydej_LogDWSplneno

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `ID_Vydejky` | int | ANO |  |  |
| 3 | `Stav_DWSplneno` | bit | ANO |  |  |
| 4 | `Odkud` | nvarchar(50) | ANO |  |  |
| 5 | `Kdo` | nvarchar(128) | ANO |  |  |
| 6 | `Kdy` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Sklad_Vydej_LogDWSplneno` (CLUSTERED) — `id`
