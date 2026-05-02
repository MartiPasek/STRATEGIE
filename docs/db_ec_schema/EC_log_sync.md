# EC_log_sync

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 3 | `DatVlozeni` | datetime | ANO | (getdate()) |  |
| 4 | `Log` | nvarchar(MAX) | ANO |  |  |
| 5 | `PocetKomplet` | int | ANO | ([dbo].[EC_GetUkolyKompletCount]()) |  |
| 6 | `PocetLoc` | int | ANO |  |  |
| 7 | `PocetKeStazeni` | int | ANO |  |  |
| 8 | `SPID` | int | ANO | (@@spid) |  |
| 9 | `IDTransakce` | int | ANO |  |  |
