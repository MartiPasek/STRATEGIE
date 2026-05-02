# EC_ImportXmlHlav

**Schema**: dbo · **Cluster**: Other · **Rows**: 49,721 · **Size**: 4.43 MB · **Sloupců**: 4 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_ImportXmlHlav` (CLUSTERED) — `ID`
