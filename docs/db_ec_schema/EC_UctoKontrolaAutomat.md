# EC_UctoKontrolaAutomat

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloOrg` | int | NE |  |  |
| 3 | `Stredisko` | nvarchar(3) | ANO |  |  |
| 4 | `TypZakazky` | nvarchar(3) | ANO |  |  |
| 5 | `Kontace` | int | ANO |  |  |
| 6 | `AutoUctovani` | bit | NE | ((0)) |  |
| 7 | `Aktivni` | bit | NE | ((1)) |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_UctoAutoUctovani` (CLUSTERED) — `ID`
