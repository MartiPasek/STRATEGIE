# EC_Dochazka_HrOdhlaseni_Temp

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `Aktivni` | bit | ANO |  |  |
| 7 | `DatDeaktivace` | datetime | ANO |  |  |
| 8 | `DruhCinnosti` | int | ANO |  |  |
| 9 | `IDPosledniDoch` | int | ANO |  |  |
