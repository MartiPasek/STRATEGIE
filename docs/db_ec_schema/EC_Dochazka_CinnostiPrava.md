# EC_Dochazka_CinnostiPrava

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DruhCinnosti` | int | ANO |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `MaPravo` | bit | ANO | ((0)) |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
