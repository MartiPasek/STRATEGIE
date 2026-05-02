# EC_OrgKvalifikaceHlav

**Schema**: dbo · **Cluster**: HR · **Rows**: 169 · **Size**: 0.14 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPost` | int | ANO |  |  |
| 3 | `Skolitel` | int | ANO |  |  |
| 4 | `Tema` | nvarchar(255) | ANO |  |  |
| 5 | `TerminZahajeni` | datetime | ANO |  |  |
| 6 | `TerminDokonceni` | datetime | ANO |  |  |
| 7 | `PocetHod` | numeric(19,2) | ANO |  |  |
| 8 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 9 | `Uzavreno` | bit | ANO |  |  |
| 10 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 11 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `IDMistnosti` | int | ANO |  |  |
