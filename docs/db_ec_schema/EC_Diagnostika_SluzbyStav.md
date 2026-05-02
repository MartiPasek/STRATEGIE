# EC_Diagnostika_SluzbyStav

**Schema**: dbo · **Cluster**: Logging · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 2 | `NazevSluzby` | nvarchar(50) | NE |  |  |
| 4 | `Citac` | int | NE |  |  |
| 5 | `CasRazitko` | datetime | ANO |  |  |
| 6 | `MqttClientNazev` | nvarchar(50) | ANO |  |  |
| 7 | `OnlineOd` | datetime | ANO |  |  |
| 8 | `EmailPoslan` | bit | ANO | ((0)) |  |
| 9 | `ID` | int | NE |  |  |

## Indexy

- **PK** `PK__EC_Diagn__3214EC2783E955FA` (CLUSTERED) — `ID`
