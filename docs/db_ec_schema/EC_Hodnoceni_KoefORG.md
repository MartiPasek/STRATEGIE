# EC_Hodnoceni_KoefORG

**Schema**: dbo · **Cluster**: HR · **Rows**: 217 · **Size**: 0.07 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloOrg` | int | ANO |  |  |
| 3 | `KoefKalk` | numeric(19,6) | ANO | ((1)) |  |
| 4 | `KoefHod` | numeric(19,6) | ANO | ((1)) |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Schvalil` | nvarchar(126) | ANO |  |  |
| 8 | `DatSchvaleni` | datetime | ANO |  |  |
| 9 | `PoznamkaZadavatel` | nvarchar(MAX) | ANO |  |  |
| 10 | `PoznamkaSchvalovatel` | nvarchar(MAX) | ANO |  |  |
| 11 | `KoefFakt` | numeric(19,6) | ANO |  |  |
| 12 | `KoefNarocnostiVP` | numeric(18,2) | NE | ((1)) |  |
| 13 | `KoefVyrobaKalkHod` | numeric(19,2) | ANO | ((1)) |  |
