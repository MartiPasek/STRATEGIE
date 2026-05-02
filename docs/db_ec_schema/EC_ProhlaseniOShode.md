# EC_ProhlaseniOShode

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,088 · **Size**: 1.06 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ZkusebniProtokol` | nvarchar(10) | NE |  |  |
| 3 | `Varianta` | int | ANO |  |  |
| 4 | `Nazev` | nvarchar(255) | ANO |  |  |
| 5 | `CisloDokumentace` | nvarchar(255) | ANO |  |  |
| 6 | `Jazyk` | nvarchar(3) | ANO | ('DE') |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `PodpisCisloZam` | int | ANO | ([dbo].[ec_getuserciszam]()) |  |
| 12 | `DatVyroby` | datetime | ANO |  |  |
| 13 | `DatVystaveni` | datetime | ANO | (getdate()) |  |
| 14 | `ID_ZP` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_ProhlaseniOShode` (CLUSTERED) — `ID`
