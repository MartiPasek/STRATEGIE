# EC_ViewSeznam

**Schema**: dbo · **Cluster**: Other · **Rows**: 11 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ViewID` | int | ANO |  |  |
| 3 | `ViewNazev` | nvarchar(100) | ANO |  |  |
| 4 | `Parametry` | nvarchar(1000) | ANO |  |  |
| 5 | `Podminka` | nvarchar(1000) | ANO |  |  |
| 6 | `ViewDef` | nvarchar(100) | ANO |  |  |
| 7 | `Procedura` | nvarchar(100) | ANO |  |  |
| 8 | `ProceduraParametry` | nvarchar(1000) | ANO |  |  |
| 9 | `NazevListu` | nvarchar(100) | ANO |  |  |

## Indexy

- **PK** `PK_EC_ViewSeznam` (CLUSTERED) — `ID`
