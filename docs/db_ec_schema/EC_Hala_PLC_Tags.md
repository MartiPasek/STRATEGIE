# EC_Hala_PLC_Tags

**Schema**: dbo · **Cluster**: Production · **Rows**: 180 · **Size**: 0.13 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `enable_interval` | bit | ANO | ((0)) |  |
| 3 | `interval` | int | ANO | ((600)) |  |
| 4 | `enable_logovani` | bit | ANO | ((0)) |  |
| 5 | `nazev_tagu` | nvarchar(100) | ANO | ('název tagu') |  |
| 6 | `popis_tagu` | nvarchar(100) | ANO | ('prázdný popis tagu') |  |
| 7 | `id_plc_connection` | int | ANO | ((1)) |  |
| 8 | `adresa_plc` | nvarchar(15) | ANO | ('') |  |
| 9 | `value_plc` | nvarchar(100) | ANO | ('') |  |
| 10 | `action_plc` | int | ANO | ((0)) |  |
| 11 | `format_plc` | int | ANO | ((3)) |  |
| 12 | `format_plc_text` | varchar(4) | ANO |  |  |
| 13 | `_run` | bit | ANO | ((0)) |  |
| 14 | `_lastdatetime` | datetime | ANO | ('2018-02-04 1:11:11.111') |  |
| 15 | `_cislo_zmeny_ServerApp` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Hala_PLC_Tags` (CLUSTERED) — `id`
