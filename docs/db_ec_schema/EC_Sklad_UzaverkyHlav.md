# EC_Sklad_UzaverkyHlav

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 30 · **Size**: 0.07 MB · **Sloupců**: 3 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Sklad_UzaverkyHlav` (CLUSTERED) — `ID`
