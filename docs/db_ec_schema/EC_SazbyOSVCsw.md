# EC_SazbyOSVCsw

**Schema**: dbo · **Cluster**: Other · **Rows**: 21 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Aktualni` | bit | NE | ((0)) |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `CisloOrg` | int | ANO |  |  |
| 5 | `SazbaVal` | numeric(18,2) | ANO | ((0)) |  |
| 6 | `SazbaKc` | numeric(18,2) | NE | ((0)) |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_SazbyOSVCsw` (CLUSTERED) — `ID`
