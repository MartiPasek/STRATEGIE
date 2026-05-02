# EC_Hala_svetla

**Schema**: dbo · **Cluster**: Production · **Rows**: 320 · **Size**: 0.13 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `idDaliG` | int | NE | ((0)) |  |
| 3 | `idDaliL` | int | NE | ((0)) |  |
| 4 | `L_mistnost` | int | NE | ((0)) |  |
| 5 | `L_sektor` | int | NE | ((0)) |  |
| 6 | `L_Def_Jas` | int | NE | ((50)) |  |
| 7 | `_popis` | nvarchar(MAX) | NE | ('') |  |

## Indexy

- **PK** `PK_EC_Hala_svetla` (CLUSTERED) — `ID`
