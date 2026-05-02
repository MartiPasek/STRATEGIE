# EC_Sklad_UzaverkyPolozky

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 67,103 · **Size**: 5.19 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | NE |  |  |
| 3 | `IDZboSklad` | int | NE |  |  |
| 4 | `Mnozstvi` | numeric(19,6) | NE | ((0)) |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_name()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Sklad_UzaverkyPolozky` (CLUSTERED) — `ID`
