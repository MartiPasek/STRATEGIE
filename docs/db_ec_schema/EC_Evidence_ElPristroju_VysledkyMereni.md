# EC_Evidence_ElPristroju_VysledkyMereni

**Schema**: dbo · **Cluster**: Other · **Rows**: 12 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDhlav` | int | ANO |  |  |
| 3 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 5 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 6 | `DatZmeny` | datetime | ANO |  |  |
| 7 | `VysledekOK` | bit | ANO |  |  |
| 8 | `Poznamka` | nvarchar(2000) | ANO |  |  |
| 9 | `EvidCisloKalibProtokolu` | nvarchar(128) | ANO |  |  |
| 10 | `DatMereni` | datetime | NE |  |  |

## Indexy

- **PK** `PK__EC_Evide__3214EC27DD081695` (CLUSTERED) — `ID`
