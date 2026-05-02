# EC_ExtKalkCena

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,605 · **Size**: 0.20 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | NE |  |  |
| 3 | `Typ` | tinyint | NE |  |  |
| 4 | `TypText` | varchar(3) | NE |  |  |
| 5 | `KalkCena` | numeric(18,2) | ANO |  |  |
| 6 | `Mena` | nvarchar(3) | NE |  |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Blokovano` | bit | NE |  |  |
| 9 | `Autor` | nvarchar(128) | NE |  |  |
| 10 | `DatPorizeni` | datetime | NE |  |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |
| 13 | `IndArchiv` | int | NE |  |  |
