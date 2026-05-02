# EC_MQTT_Zpravy

**Schema**: dbo · **Cluster**: Other · **Rows**: 25,229 · **Size**: 4.09 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `OdKoho` | nvarchar(50) | ANO |  |  |
| 3 | `PacketID` | int | ANO |  |  |
| 4 | `Topic` | nvarchar(200) | ANO |  |  |
| 5 | `Zprava` | nvarchar(MAX) | ANO |  |  |
| 6 | `Qos` | int | ANO |  |  |
| 7 | `Retain` | bit | ANO |  |  |
| 8 | `Expire` | int | ANO |  |  |
| 9 | `OdeslanoNaSQLServer` | bit | ANO |  |  |
| 10 | `PotvrzenoSQLServerem` | bit | ANO |  |  |
| 11 | `Archiv` | bit | NE | ((0)) |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_MQTT_Zpravy` (CLUSTERED) — `ID`
