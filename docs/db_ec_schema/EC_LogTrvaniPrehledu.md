# EC_LogTrvaniPrehledu

**Schema**: dbo · **Cluster**: Logging · **Rows**: 83,715 · **Size**: 5.66 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloPrehledu` | int | ANO |  |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `CasZacatek` | datetime | ANO |  |  |
| 6 | `CasKonec` | datetime | ANO |  |  |
