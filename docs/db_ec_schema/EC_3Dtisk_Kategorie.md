# EC_3Dtisk_Kategorie

**Schema**: dbo · **Cluster**: Other · **Rows**: 16 · **Size**: 0.08 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDNadrazene` | int | ANO | ((0)) |  |
| 3 | `Nazev` | nvarchar(50) | NE |  |  |
| 4 | `Popis` | nvarchar(250) | ANO |  |  |
| 5 | `Typ` | nvarchar(20) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_3Dtisk_Kategorie` (CLUSTERED) — `ID`
