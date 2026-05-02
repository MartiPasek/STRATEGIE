# EC_GarantiOrganizace

**Schema**: dbo · **Cluster**: Finance · **Rows**: 26 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `CisloOrg` | int | NE |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_name()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Zkratka` | nvarchar(15) | ANO |  |  |

## Indexy

- **PK** `PK_EC_GarantiOrganizace` (CLUSTERED) — `ID`
