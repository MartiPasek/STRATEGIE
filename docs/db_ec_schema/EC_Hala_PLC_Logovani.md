# EC_Hala_PLC_Logovani

**Schema**: dbo · **Cluster**: Production · **Rows**: 312 · **Size**: 0.33 MB · **Sloupců**: 4 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `nazev_tagu` | nvarchar(100) | NE | ('') |  |
| 3 | `value_plc` | nvarchar(50) | NE | ('') |  |
| 4 | `date` | nvarchar(50) | NE | ('') |  |

## Indexy

- **PK** `PK_EC_Hala_PLC_Logovani` (CLUSTERED) — `id`
