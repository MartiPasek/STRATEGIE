# EC_IT_SeznamHW

**Schema**: dbo · **Cluster**: Other · **Rows**: 4 · **Size**: 0.07 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Id_PC` | int | ANO |  |  |
| 3 | `Id_Typ` | nvarchar(30) | ANO |  |  |
| 4 | `Id_Vyrobce` | nvarchar(30) | ANO |  |  |
| 5 | `Model` | nvarchar(30) | ANO |  |  |
| 6 | `SN` | nvarchar(100) | ANO |  |  |
| 7 | `Mac_LAN` | nvarchar(17) | ANO |  |  |
| 8 | `Mac_WLAN` | nvarchar(17) | ANO |  |  |
| 9 | `IP` | nvarchar(15) | ANO |  |  |
| 10 | `Id_Umisteni` | nvarchar(100) | ANO |  |  |
| 11 | `Velikost` | nvarchar(30) | ANO |  |  |
| 12 | `Popis` | nvarchar(150) | ANO |  |  |
| 13 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 14 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 15 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 16 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_IT_SeznamHW` (CLUSTERED) — `Id`
