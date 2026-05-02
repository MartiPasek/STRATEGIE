# EC_TabSeznamID

**Schema**: dbo · **Cluster**: Finance · **Rows**: 107 · **Size**: 0.23 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `OK` | bit | NE | ((0)) |  |
| 3 | `ID2` | int | ANO |  |  |
| 4 | `MnozstviZbyva` | numeric(18,2) | ANO |  |  |
| 5 | `Mnozstvi` | numeric(18,2) | ANO |  |  |
| 6 | `JCbezDaniVal` | numeric(18,6) | ANO |  |  |
| 7 | `JCbezDaniKc` | numeric(18,6) | ANO |  |  |
| 8 | `CCbezDaniVal` | numeric(18,6) | ANO |  |  |
| 9 | `CCbezDaniKc` | numeric(18,6) | ANO |  |  |
| 10 | `MnozstviPonechatNaSklade` | numeric(18,6) | ANO |  |  |
| 11 | `MnozstviNavysenoNaZakazku` | numeric(18,6) | NE | ((0)) |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
