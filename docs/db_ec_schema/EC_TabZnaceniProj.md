# EC_TabZnaceniProj

**Schema**: dbo · **Cluster**: Finance · **Rows**: 655 · **Size**: 0.20 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDdok` | int | ANO |  |  |
| 3 | `CisloProjektu` | nvarchar(50) | ANO |  |  |
| 4 | `Nazev` | nvarchar(50) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_TabZnaceniProj` (CLUSTERED) — `ID`
