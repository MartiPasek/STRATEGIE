# EC_SW

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(50) | ANO |  |  |
| 3 | `NazevEXEsouboru` | nvarchar(24) | ANO |  |  |
| 4 | `NazevSouboruArchivuDev` | nvarchar(24) | ANO |  |  |
| 5 | `NazevSouboruArchivuRT` | nvarchar(24) | ANO |  |  |
| 6 | `AdresarArchivuDev` | nvarchar(200) | ANO |  |  |
| 7 | `AdresarArchivuRT` | nvarchar(200) | ANO |  |  |
| 8 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 9 | `TypSW` | nvarchar(20) | ANO |  |  |
| 10 | `BlokovatNepovoleneUziv` | bit | NE | ((0)) |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_SW` (CLUSTERED) — `ID`
