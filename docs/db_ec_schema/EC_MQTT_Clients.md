# EC_MQTT_Clients

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ClientID` | nvarchar(50) | ANO |  |  |
| 3 | `ClientSN` | nvarchar(100) | ANO |  |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `Login` | nvarchar(50) | ANO | ((0)) |  |
| 6 | `TypAplikace` | int | ANO |  |  |
| 7 | `ClientWill` | nvarchar(200) | ANO |  |  |
| 8 | `ClientText` | nvarchar(200) | ANO |  |  |
| 9 | `Autorizovan` | tinyint | NE | ((0)) |  |
| 10 | `Aktivni` | bit | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_MQTT_Clients` (CLUSTERED) — `ID`
