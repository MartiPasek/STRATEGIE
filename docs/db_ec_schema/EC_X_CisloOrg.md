# EC_X_CisloOrg

**Schema**: dbo · **Cluster**: Other · **Rows**: 11 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo1` | int | ANO |  |  |
| 3 | `Cislo2` | int | ANO |  |  |
| 4 | `Firma` | nvarchar(200) | ANO |  |  |
| 5 | `Poznamka` | nvarchar(400) | ANO |  |  |
| 6 | `Blokovano` | bit | NE | ((0)) |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_X_CisloOrg` (CLUSTERED) — `ID`
