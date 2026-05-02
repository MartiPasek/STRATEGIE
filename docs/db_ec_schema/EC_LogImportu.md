# EC_LogImportu

**Schema**: dbo · **Cluster**: Logging · **Rows**: 747 · **Size**: 0.21 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDImportu` | int | ANO |  |  |
| 3 | `DatumImportu` | datetime | ANO | (getdate()) |  |
| 4 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 6 | `Procedura` | nvarchar(100) | ANO |  |  |
| 7 | `Zacatek` | bit | ANO | ((0)) |  |
| 8 | `Konec` | bit | ANO | ((0)) |  |
