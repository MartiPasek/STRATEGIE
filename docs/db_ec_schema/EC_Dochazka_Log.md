# EC_Dochazka_Log

**Schema**: dbo · **Cluster**: HR · **Rows**: 743,054 · **Size**: 73.58 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `TypAkce` | int | NE |  |  |
| 4 | `Cinnost` | int | ANO |  |  |
| 5 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Dochazka_Log` (CLUSTERED) — `ID`
