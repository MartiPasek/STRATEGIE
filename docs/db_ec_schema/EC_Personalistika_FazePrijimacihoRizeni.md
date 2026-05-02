# EC_Personalistika_FazePrijimacihoRizeni

**Schema**: dbo · **Cluster**: HR · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | ANO |  |  |
| 3 | `Faze` | nvarchar(200) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Personalistika_FazePrijmacihoRizeni` (CLUSTERED) — `ID`
