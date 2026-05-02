# EC_GridSelectedRows

**Schema**: dbo · **Cluster**: Other · **Rows**: 35,758 · **Size**: 8.28 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `GUID` | uniqueidentifier | NE |  |  |
| 2 | `FieldName` | nvarchar(128) | ANO | ('ID') |  |
| 3 | `FieldValue` | int | NE |  |  |
| 4 | `ViewNumber` | int | NE |  |  |
| 5 | `GridName` | nvarchar(128) | NE |  |  |
| 6 | `FormName` | nvarchar(128) | NE |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
