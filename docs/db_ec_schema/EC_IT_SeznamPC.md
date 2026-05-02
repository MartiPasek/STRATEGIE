# EC_IT_SeznamPC

**Schema**: dbo · **Cluster**: Other · **Rows**: 4 · **Size**: 0.07 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Id_Typ` | int | ANO |  |  |
| 3 | `Id_Vyrobce` | int | ANO |  |  |
| 4 | `Model` | nvarchar(30) | ANO |  |  |
| 5 | `Uzivatel` | nvarchar(100) | ANO |  |  |
| 6 | `SN` | nvarchar(100) | ANO |  |  |
| 7 | `Mac_LAN` | nvarchar(17) | ANO |  |  |
| 8 | `Mac_WLAN` | nvarchar(17) | ANO |  |  |
| 9 | `IP` | nvarchar(15) | ANO |  |  |
| 10 | `Id_Umisteni` | int | ANO |  |  |
| 11 | `Velikost` | nvarchar(30) | ANO |  |  |
| 12 | `Popis` | nvarchar(150) | ANO |  |  |
| 13 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 14 | `Datum_zalohy` | datetime | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 18 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_IT_SeznamPC` (CLUSTERED) — `Id`
