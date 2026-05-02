# EC_ZamSkupinyHodn

**Schema**: dbo · **Cluster**: Other · **Rows**: 72 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Skupina` | nvarchar(50) | ANO |  |  |
| 4 | `ZkratkaSk` | nvarchar(20) | ANO |  |  |
| 5 | `Popis` | nvarchar(200) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZamSkupinyHodn` (CLUSTERED) — `ID`
