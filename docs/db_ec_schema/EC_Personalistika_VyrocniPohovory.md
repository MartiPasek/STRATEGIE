# EC_Personalistika_VyrocniPohovory

**Schema**: dbo · **Cluster**: HR · **Rows**: 41 · **Size**: 0.27 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `DatPohovoru` | datetime | ANO |  |  |
| 4 | `Popis` | ntext | ANO |  |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Personalistika_VyrocniPohovory` (CLUSTERED) — `ID`
