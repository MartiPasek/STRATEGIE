# EC_Banka_uhrady_temp

**Schema**: dbo · **Cluster**: Finance · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 3 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPolBV` | nchar(10) | NE |  |  |
| 3 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_Banka_uhrady_temp` (CLUSTERED) — `ID`
