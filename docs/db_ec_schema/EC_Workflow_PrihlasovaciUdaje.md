# EC_Workflow_PrihlasovaciUdaje

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | NE |  |  |
| 3 | `TypPrihlasovacihoUdaje` | nvarchar(50) | NE |  |  |
| 4 | `Konfigurace` | nvarchar(MAX) | ANO |  |  |
| 5 | `TajnyKlic` | nvarchar(200) | ANO |  |  |
| 6 | `Aktivni` | bit | NE | ((1)) |  |
| 7 | `DatumVytvoreni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK__EC_Workf__3214EC076AE10459` (CLUSTERED) — `Id`
