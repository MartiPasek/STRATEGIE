# EC_Dochazka_KontrolaPravidelna

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 3 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `Typ` | int | ANO |  |  |
| 6 | `IdDoch` | int | ANO |  |  |
| 7 | `CasZacatek` | datetime | ANO |  |  |
| 8 | `DruhCinnosti` | int | ANO |  |  |
