# EC_Evidence_ElPristroju_RozsahyMereni

**Schema**: dbo · **Cluster**: Other · **Rows**: 35 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `OD` | numeric(10,3) | ANO |  |  |
| 3 | `OD_Jednotka` | nvarchar(10) | ANO |  |  |
| 4 | `DO` | numeric(10,3) | ANO |  |  |
| 5 | `DO_Jednotka` | nvarchar(10) | ANO |  |  |
| 6 | `Velicina` | nvarchar(100) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `IDhlav` | int | ANO |  |  |
| 13 | `Presnost` | numeric(10,3) | ANO |  |  |

## Indexy

- **PK** `PK__EC_Evide__3214EC270AB56BDE` (CLUSTERED) — `ID`
