# EC_JednaniVazby

**Schema**: dbo · **Cluster**: CRM · **Rows**: 354 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | tinyint | ANO |  |  |
| 3 | `CisloOrg` | int | ANO |  |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `CisloKos` | int | ANO |  |  |
| 6 | `IDJednani` | int | ANO |  |  |
| 7 | `Poznamka` | nvarchar(255) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 11 | `DatZmeny` | datetime | ANO | (getdate()) |  |
