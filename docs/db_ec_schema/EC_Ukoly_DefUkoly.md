# EC_Ukoly_DefUkoly

**Schema**: dbo · **Cluster**: Other · **Rows**: 97 · **Size**: 0.14 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `OdesliVedoucimu` | bit | NE | ((0)) |  |
| 3 | `Nazev` | nvarchar(100) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `Predmet` | nvarchar(255) | ANO |  |  |
| 7 | `Popis` | ntext | ANO |  |  |
| 8 | `Zadavatel` | int | ANO | (NULL) |  |
| 9 | `TerminSplneni_Typ` | int | ANO |  |  |
| 10 | `TerminSplneni_TypText` | varchar(36) | NE |  |  |
| 11 | `TerminSplneni_Pocet` | int | ANO |  |  |
| 12 | `KontrolaNepritomnosti` | bit | ANO | ((1)) |  |
| 13 | `PotvrdUkol_PoDokonceni` | bit | ANO | ((0)) |  |
| 14 | `NeBlokovatDochZadavatel` | bit | ANO | ((0)) |  |
| 15 | `NeBlokovatDochResitel` | bit | ANO | ((0)) |  |
