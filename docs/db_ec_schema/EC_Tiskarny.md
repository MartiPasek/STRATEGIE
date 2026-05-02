# EC_Tiskarny

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 3 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 4 | `DatZmeny` | datetime | ANO |  |  |
| 5 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 6 | `Name` | nvarchar(200) | ANO |  |  |
| 7 | `IP_address` | nvarchar(50) | ANO |  |  |
| 8 | `Type` | nvarchar(20) | ANO |  |  |
| 9 | `Location` | nvarchar(20) | ANO |  |  |
| 10 | `Floor` | nvarchar(10) | ANO |  |  |
| 11 | `Snmp_community` | nvarchar(10) | ANO |  |  |
| 12 | `Snmp_version` | int | ANO |  |  |
| 13 | `Visible_dashboard` | bit | ANO |  |  |
| 14 | `Created_at` | datetime | ANO |  |  |
| 15 | `Updated_at` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Tiskarny` (CLUSTERED) — `ID`
