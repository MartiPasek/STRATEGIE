# EC_SkoleniBOZPPOStudenti

**Schema**: dbo · **Cluster**: HR · **Rows**: 274 · **Size**: 0.20 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloStudent` | int | ANO |  |  |
| 3 | `CisloSkolitel` | int | ANO |  |  |
| 4 | `DruhSkoleni` | nvarchar(200) | ANO |  |  |
| 5 | `DatSkoleni` | datetime | ANO |  |  |
| 6 | `DatDalsiSkoleni` | datetime | ANO |  |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatZmeny` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_SkoleniBOZPPOStudenti` (CLUSTERED) — `ID`
