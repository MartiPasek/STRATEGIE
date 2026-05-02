# EC_Kontakt_DNB

**Schema**: dbo · **Cluster**: CRM · **Rows**: 0 · **Size**: 0.20 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `NazevFirmy` | nvarchar(255) | NE |  |  |
| 3 | `Odvetvi` | nvarchar(100) | ANO |  |  |
| 4 | `Mesto` | nvarchar(100) | ANO |  |  |
| 5 | `Oblast` | nvarchar(100) | ANO |  |  |
| 6 | `Zeme` | nvarchar(50) | ANO |  |  |
| 7 | `TrzbyEUR_M` | decimal(10,1) | ANO |  |  |
| 8 | `TrzbyOdhad` | bit | NE | ((0)) |  |
| 9 | `PocetZamestnancuSite` | int | ANO |  |  |
| 10 | `TypSpolecnosti` | nvarchar(50) | ANO |  |  |
| 11 | `Telefon` | nvarchar(50) | ANO |  |  |
| 12 | `Web` | nvarchar(150) | ANO |  |  |
| 13 | `DatumImportu` | datetime | NE | (getdate()) |  |
| 14 | `Zpracovano` | bit | NE | ((0)) |  |
| 15 | `TEXTadd` | nvarchar(200) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Kontakt_DNB` (CLUSTERED) — `ID`
