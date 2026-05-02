# EC_Intrastat_KodyNomenklatury

**Schema**: dbo · **Cluster**: Other · **Rows**: 16 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Neaktivni` | bit | NE | ((0)) |  |
| 3 | `KodKN` | char(8) | NE |  |  |
| 4 | `PopisCZ` | nvarchar(255) | ANO |  |  |
| 5 | `PopisEN` | nvarchar(255) | ANO |  |  |
| 6 | `MJ` | nvarchar(10) | ANO |  |  |
| 7 | `PlatnostOd` | date | ANO |  |  |
| 8 | `PlatnostDo` | date | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK__EC_Intra__3214EC278CE2B607` (CLUSTERED) — `ID`
