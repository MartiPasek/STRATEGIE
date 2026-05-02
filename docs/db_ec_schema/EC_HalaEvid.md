# EC_HalaEvid

**Schema**: dbo · **Cluster**: Production · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_MistnostObjekt` | int | ANO |  |  |
| 3 | `ID_Skupina` | int | ANO |  |  |
| 4 | `Popis` | nvarchar(128) | ANO |  |  |
| 5 | `CasDokonceni` | datetime | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_HalaEvid` (CLUSTERED) — `ID`
