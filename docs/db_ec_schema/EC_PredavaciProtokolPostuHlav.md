# EC_PredavaciProtokolPostuHlav

**Schema**: dbo · **Cluster**: Production · **Rows**: 157 · **Size**: 0.13 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloPostu` | int | ANO |  |  |
| 3 | `NazevPostu` | nvarchar(200) | ANO |  |  |
| 4 | `Prebirajici` | int | ANO |  |  |
| 5 | `Predavajici` | int | ANO |  |  |
| 6 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 7 | `DatZahajeni` | datetime | ANO |  |  |
| 8 | `DatUkonceni` | datetime | ANO |  |  |
| 9 | `ZodpovednaOsoba` | int | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 13 | `DatZmeny` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_KvalifikacniPredavaciProtokol` (CLUSTERED) — `ID`
