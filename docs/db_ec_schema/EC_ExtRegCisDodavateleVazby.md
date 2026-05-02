# EC_ExtRegCisDodavateleVazby

**Schema**: dbo · **Cluster**: Other · **Rows**: 11 · **Size**: 0.02 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `RegCisZkratka` | nvarchar(8) | NE |  |  |
| 3 | `CisloOrg` | int | ANO |  |  |
| 4 | `Poradi` | tinyint | NE |  |  |
| 5 | `Vychozi` | bit | NE |  |  |
| 6 | `Blokovano` | bit | NE |  |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE |  |  |
| 9 | `DatPorizeni` | datetime | NE |  |  |
| 10 | `DatZamceni` | datetime | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |
