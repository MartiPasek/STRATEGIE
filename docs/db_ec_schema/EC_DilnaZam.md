# EC_DilnaZam

**Schema**: dbo · **Cluster**: Other · **Rows**: 18 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `Prijmeni` | nvarchar(50) | ANO |  |  |
| 4 | `Sluzba` | nvarchar(2) | ANO |  |  |
| 5 | `PosledniSluzba` | date | ANO |  |  |
| 6 | `Poznamka` | nvarchar(50) | ANO |  |  |
| 7 | `DatumZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_DilnaSluzbySum` (CLUSTERED) — `ID`
