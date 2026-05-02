# EC_ZamJubilea

**Schema**: dbo · **Cluster**: Other · **Rows**: 157 · **Size**: 0.08 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Udalost` | nvarchar(50) | ANO |  |  |
| 4 | `Den` | int | ANO |  |  |
| 5 | `Mesic` | int | ANO |  |  |
| 6 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ZamJubilea` (CLUSTERED) — `ID`
