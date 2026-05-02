# EC_MQTT_Subscribe

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Topic` | nvarchar(200) | ANO |  |  |
| 3 | `ClientID` | nvarchar(50) | NE |  |  |
| 4 | `Typ` | int | ANO |  |  |
| 5 | `Komponenta` | nvarchar(50) | ANO |  |  |
| 6 | `Aktivni` | bit | NE | ((1)) |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_MQTT_Subscribe` (CLUSTERED) — `ID`
