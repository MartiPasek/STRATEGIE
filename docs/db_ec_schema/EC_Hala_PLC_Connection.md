# EC_Hala_PLC_Connection

**Schema**: dbo · **Cluster**: Production · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `Popis_plc` | nvarchar(500) | ANO |  |  |
| 3 | `IP` | nvarchar(50) | ANO | ('0.0.0.0') |  |
| 4 | `_rack` | int | NE | ((0)) |  |
| 5 | `_slot` | int | NE | ((0)) |  |
| 6 | `_connType` | int | NE | ((1)) |  |
| 7 | `_connType_text` | varchar(12) | NE |  |  |
| 8 | `_ping` | bit | NE | ((1)) |  |
| 9 | `_ping_text` | varchar(12) | NE |  |  |
| 10 | `_mode` | int | NE | ((0)) |  |
| 11 | `_mode_text` | varchar(17) | NE |  |  |

## Indexy

- **PK** `PK_EC_Hala_PLC_connecion` (CLUSTERED) — `id`
