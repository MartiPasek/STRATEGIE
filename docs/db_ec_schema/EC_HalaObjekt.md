# EC_HalaObjekt

**Schema**: dbo · **Cluster**: Production · **Rows**: 4 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `MistnostObjekt` | nvarchar(70) | NE |  |  |
| 3 | `ID_NadrazenyObjekt` | int | ANO |  |  |
| 4 | `NazevStavba` | nvarchar(50) | ANO |  |  |
| 5 | `NazevEC` | nvarchar(50) | ANO |  |  |
| 6 | `Popis` | nvarchar(128) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_HalaObjekt` (CLUSTERED) — `ID`
