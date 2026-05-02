# EC_KalkSestavySkup

**Schema**: dbo · **Cluster**: Production · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloOrg` | int | ANO |  |  |
| 3 | `Nazev` | nvarchar(200) | NE | (N'!!! Doplň název !!!') |  |
| 4 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 5 | `Status` | tinyint | NE | ((0)) |  |
| 6 | `StatusText` | varchar(15) | NE |  |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_KalkStandard` (CLUSTERED) — `ID`
