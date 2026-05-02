# EC_Hala_PLC

**Schema**: dbo · **Cluster**: Production · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ip` | nvarchar(16) | NE | ('0.0.0.0') |  |
| 3 | `ping` | bit | NE | ((1)) |  |
| 4 | `rack` | int | NE | ((0)) |  |
| 5 | `slot` | int | NE | ((2)) |  |
| 6 | `connType` | int | NE | ((1)) | //1-pg , 2-op nebo 3-S7basic//  vzor program Snap7 Client Demo |
| 7 | `mode` | int | NE |  |  |
| 8 | `_popis` | nvarchar(MAX) | NE | ('') |  |

## Indexy

- **PK** `PK_EC_Hala_PLC` (CLUSTERED) — `ID`
