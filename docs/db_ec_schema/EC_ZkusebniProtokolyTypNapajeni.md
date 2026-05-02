# EC_ZkusebniProtokolyTypNapajeni

**Schema**: dbo · **Cluster**: Other · **Rows**: 12 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `TypNapajeni` | nchar(50) | ANO |  |  |
| 3 | `Napajeni_ID` | int | ANO |  |  |
| 4 | `RiNapeti1_ID` | int | ANO |  |  |
| 5 | `RiNapeti2_ID` | int | ANO |  |  |
| 6 | `RiNapeti3_ID` | int | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_name()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `Poznamka` | nvarchar(200) | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZkusebniProtokolyTypNapajeni` (CLUSTERED) — `ID`
