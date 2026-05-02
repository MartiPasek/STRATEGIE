# EC_TabCisUctC

**Schema**: dbo · **Cluster**: Finance · **Rows**: 39 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloUcet` | int | ANO |  |  |
| 3 | `ZkratkaUctu` | nvarchar(10) | ANO |  |  |
| 4 | `NazevUctu` | nvarchar(50) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_TabCisUctC` (CLUSTERED) — `ID`
