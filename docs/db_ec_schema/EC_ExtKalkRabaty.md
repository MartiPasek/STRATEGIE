# EC_ExtKalkRabaty

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,843 · **Size**: 0.20 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | NE |  |  |
| 3 | `Typ` | tinyint | NE |  |  |
| 4 | `TypText` | varchar(8) | NE |  |  |
| 5 | `Rabat` | numeric(6,1) | ANO |  |  |
| 6 | `CisloOrg` | int | ANO |  |  |
| 7 | `CisloOrgDod` | int | ANO |  |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `Blokovano` | bit | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE |  |  |
| 11 | `DatPorizeni` | datetime | NE |  |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `IndArchiv` | int | NE |  |  |
