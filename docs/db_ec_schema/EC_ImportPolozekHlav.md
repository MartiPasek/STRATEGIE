# EC_ImportPolozekHlav

**Schema**: dbo · **Cluster**: Other · **Rows**: 138,343 · **Size**: 11.63 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | int | ANO |  |  |
| 3 | `Zpracovano` | bit | ANO |  |  |
| 4 | `DatZpracovani` | datetime | ANO |  |  |
| 5 | `CisloOrg` | int | ANO |  |  |
| 6 | `PoradoveCislo` | int | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `CisloDokladu` | nvarchar(126) | ANO |  |  |
| 10 | `IDZdroj` | int | ANO |  |  |
| 11 | `NavaznaObjednavka` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_ImportPolozekHlav` (CLUSTERED) — `ID`
