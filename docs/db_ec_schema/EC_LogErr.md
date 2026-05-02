# EC_LogErr

**Schema**: dbo · **Cluster**: Logging · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Text` | nvarchar(200) | ANO |  |  |
| 3 | `SQL_Text` | nvarchar(4000) | ANO |  |  |
| 4 | `ERR_Text` | nvarchar(4000) | ANO |  |  |
| 5 | `Zpracovano` | bit | NE | ((0)) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime2 | NE | (getdate()) |  |
