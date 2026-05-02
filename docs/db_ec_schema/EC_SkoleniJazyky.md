# EC_SkoleniJazyky

**Schema**: dbo · **Cluster**: HR · **Rows**: 108 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `TrvaniOd` | datetime | ANO |  |  |
| 4 | `TrvaniDo` | datetime | ANO |  |  |
| 5 | `Jazyk` | nvarchar(50) | ANO |  |  |
| 6 | `Pokrocilost` | nvarchar(50) | ANO |  |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 11 | `DatZmeny` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ZamSkoleniJazyky` (CLUSTERED) — `ID`
