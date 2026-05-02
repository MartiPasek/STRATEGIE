# EC_ZakazkyVzoryVazby

**Schema**: dbo · **Cluster**: Finance · **Rows**: 14 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDZdroj` | int | ANO |  |  |
| 3 | `IDCil` | int | ANO |  |  |
| 4 | `Typ` | int | ANO |  | 1 = Vazby na položky Mustru průběhu zabázky |
| 5 | `Skupina` | smallint | ANO |  | Obecný, specifický pro zákazníka... |
| 6 | `Poznamka` | nvarchar(255) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
