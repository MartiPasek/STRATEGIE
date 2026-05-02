# EC_KalkSkupinyZalohaNesahat

**Schema**: dbo · **Cluster**: Production · **Rows**: 115 · **Size**: 0.02 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | ANO |  |  |
| 3 | `Nazev` | nvarchar(200) | ANO |  |  |
| 4 | `Poradi` | int | ANO |  |  |
| 5 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 6 | `Zamceno` | bit | NE |  |  |
| 7 | `Autor` | nvarchar(128) | NE |  |  |
| 8 | `DatPorizeni` | datetime | NE |  |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 12 | `DatZamceni` | datetime | ANO |  |  |
