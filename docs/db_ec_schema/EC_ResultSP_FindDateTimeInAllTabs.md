# EC_ResultSP_FindDateTimeInAllTabs

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `HledanyText` | nvarchar(100) | ANO |  |  |
| 2 | `TableName` | nvarchar(1000) | ANO |  |  |
| 3 | `Count_StrFind` | int | ANO |  |  |
| 4 | `ViewSelect` | nvarchar(4000) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatumVytvoreni` | datetime | NE | (getdate()) |  |
| 7 | `NazevSloupecku` | nvarchar(100) | ANO |  |  |
