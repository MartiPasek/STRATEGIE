# EC_3Dtisk_Modely

**Schema**: dbo · **Cluster**: Other · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKategorie` | int | ANO |  |  |
| 3 | `Nazev` | nvarchar(50) | NE |  |  |
| 4 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 5 | `Adresar` | nvarchar(150) | ANO |  |  |
| 6 | `Multifilament` | bit | NE | ((0)) |  |
| 7 | `Podpory` | bit | NE | ((0)) |  |
| 8 | `Typ` | nvarchar(20) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_3Dtisk_Modely` (CLUSTERED) — `ID`
