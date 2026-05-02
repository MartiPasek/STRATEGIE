# EC_PersonalistikaSkoly

**Schema**: dbo · **Cluster**: HR · **Rows**: 41 · **Size**: 0.07 MB · **Sloupců**: 4 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `NazevSkoly` | nvarchar(300) | ANO |  |  |
| 3 | `AdresaSkolyUlice` | nvarchar(300) | ANO |  |  |
| 4 | `AdresaSkolyMesto` | nvarchar(300) | ANO |  |  |

## Indexy

- **PK** `PK_EC_PersonalistikaSkoly` (CLUSTERED) — `ID`
