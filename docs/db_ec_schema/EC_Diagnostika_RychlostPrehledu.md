# EC_Diagnostika_RychlostPrehledu

**Schema**: dbo · **Cluster**: Logging · **Rows**: 2,349,082 · **Size**: 209.65 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Autor` | nvarchar(20) | NE |  |  |
| 2 | `ID` | int | NE |  |  |
| 3 | `CisloPrehledu` | int | NE |  |  |
| 4 | `SPID` | int | NE |  |  |
| 5 | `DatPorizeni` | datetime | NE |  |  |
| 6 | `Vytvoreni` | int | NE |  |  |
| 7 | `Init` | int | NE |  |  |
| 8 | `Prava` | int | NE |  |  |
| 9 | `PopupMenu` | int | NE |  |  |
| 10 | `Nastav` | int | NE |  |  |
| 11 | `Filter_nacteni` | int | NE |  |  |
| 12 | `Filter_vytvoreni` | int | NE |  |  |
| 13 | `Filter_vykresleni` | int | NE |  |  |
| 14 | `RestorePos` | int | NE |  |  |
| 15 | `DataSource` | int | NE |  |  |
| 16 | `Footer` | int | NE |  |  |

## Indexy

- **PK** `PK_EC_Diagnostika_RychlostPrehledu` (CLUSTERED) — `ID`
