# EC_KalkSkupinyPolozkyZalohaNesahat

**Schema**: dbo · **Cluster**: Production · **Rows**: 1,672 · **Size**: 0.13 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Skupina` | int | ANO |  |  |
| 3 | `IDKmenZbozi` | int | ANO |  |  |
| 4 | `Poradi` | int | ANO |  |  |
| 5 | `DatZamceni` | datetime | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE |  |  |
| 7 | `DatPorizeni` | datetime | NE |  |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 11 | `Zamceno` | bit | NE |  |  |
