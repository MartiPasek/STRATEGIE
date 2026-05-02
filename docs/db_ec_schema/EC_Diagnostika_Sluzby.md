# EC_Diagnostika_Sluzby

**Schema**: dbo · **Cluster**: Logging · **Rows**: 9 · **Size**: 0.09 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `NazevSluzby` | nvarchar(50) | NE |  |  |
| 2 | `CestaKeSluzbe` | nvarchar(100) | NE |  |  |
| 3 | `PIN` | nvarchar(10) | NE |  |  |
| 4 | `Aktivni` | bit | NE |  |  |
| 5 | `Druh` | smallint | NE |  |  |
| 6 | `OdlozenyStart` | time | ANO |  |  |
| 7 | `PeriodickyRestart` | time | ANO |  |  |
| 8 | `KontrolujMQTT` | bit | ANO |  |  |
