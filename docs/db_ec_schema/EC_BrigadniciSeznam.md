# EC_BrigadniciSeznam

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `PrijmeniJmeno` | nvarchar(402) | ANO |  |  |
| 4 | `DatumOd` | date | ANO |  |  |
| 5 | `DatumDo` | date | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `NazevZam` | nvarchar(200) | ANO |  |  |

## Indexy

- **PK** `PK_EC_BrigadniciSeznam` (CLUSTERED) — `ID`
