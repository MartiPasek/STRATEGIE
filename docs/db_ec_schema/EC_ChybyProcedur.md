# EC_ChybyProcedur

**Schema**: dbo · **Cluster**: Logging · **Rows**: 6,159 · **Size**: 6.76 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Nazev` | nvarchar(MAX) | NE |  |  |
| 2 | `Params` | nvarchar(MAX) | NE |  |  |
| 3 | `Chyba` | nvarchar(MAX) | NE |  |  |
| 4 | `ObjectChyby` | nvarchar(MAX) | ANO |  |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `ID` | int | NE |  |  |

## Indexy

- **PK** `PK_EC_ChybyProcedur` (CLUSTERED) — `ID`
