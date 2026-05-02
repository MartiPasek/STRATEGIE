# EC_KalkulacePolozky_TempObjSklad

**Schema**: dbo · **Cluster**: Production · **Rows**: 2,124 · **Size**: 0.26 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `RegCis` | nvarchar(30) | NE |  |  |
| 2 | `Mnozstvi` | numeric(38,6) | NE |  |  |
| 3 | `MnozstviStorno` | numeric(38,6) | NE |  |  |
| 4 | `MnOdebrane` | numeric(38,6) | NE |  |  |
| 5 | `DruhPohybuZbo` | tinyint | NE |  |  |
| 6 | `Splneno` | int | ANO |  |  |
| 7 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
