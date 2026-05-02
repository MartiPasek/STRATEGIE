# EC_3Dtisk_Material

**Schema**: dbo · **Cluster**: Other · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(50) | NE |  |  |
| 3 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 4 | `Typ` | nvarchar(20) | ANO |  |  |
| 5 | `MJ` | nchar(10) | NE |  |  |
| 6 | `Mnozstvi` | int | NE |  |  |
| 7 | `Parametr1` | nvarchar(20) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_3Dtisk_material` (CLUSTERED) — `ID`
