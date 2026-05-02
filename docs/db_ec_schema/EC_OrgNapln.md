# EC_OrgNapln

**Schema**: dbo · **Cluster**: HR · **Rows**: 404 · **Size**: 0.13 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | NE | ((-1)) |  |
| 3 | `Nazev` | nvarchar(255) | ANO |  |  |
| 4 | `IDCinnost` | int | ANO |  |  |
| 6 | `Poznamka` | nvarchar(255) | ANO | ('') |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_OrgNapln` (CLUSTERED) — `ID`
