# EC_AsynchProceduryStatus

**Schema**: dbo · **Cluster**: Logging · **Rows**: 55,401 · **Size**: 9.32 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | NE |  |  |
| 3 | `Status` | int | NE |  |  |
| 4 | `StatusText` | nvarchar(200) | ANO |  |  |
| 5 | `CasSpusteni` | datetime | ANO |  |  |
| 6 | `CasPrubehu` | datetime | ANO |  |  |
| 7 | `CasPreruseniChybou` | datetime | ANO |  |  |
| 8 | `CasUkonceni` | datetime | ANO |  |  |
| 9 | `PocetKroku` | int | ANO |  |  |
| 10 | `AktualniKrok` | int | ANO |  |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_AsynchProceduryStatus` (CLUSTERED) — `ID`
