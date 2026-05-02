# EC_IAP_OldFotoAdr

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 3 | `DirName` | nvarchar(MAX) | ANO |  |  |
| 4 | `DirPath` | nvarchar(MAX) | ANO |  |  |
| 5 | `DirDate` | datetime | ANO |  |  |
| 6 | `DirLevel` | int | ANO |  |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_IAP_OldFotoAdr` (CLUSTERED) — `ID`
