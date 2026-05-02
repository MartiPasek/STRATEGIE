# EC_PredavaciProtokolPostuPol_ARCHIV

**Schema**: dbo · **Cluster**: Production · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPuv` | int | ANO |  |  |
| 3 | `IDHlav` | int | ANO |  |  |
| 4 | `Poradi` | int | ANO |  |  |
| 5 | `Cinnost` | nvarchar(200) | ANO |  |  |
| 6 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 7 | `PredanoProcent` | numeric(18,0) | ANO |  |  |
| 8 | `DatPodpisuPredavajiciho` | datetime | ANO |  |  |
| 9 | `DatPodpisuPrebirajiciho` | datetime | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | ANO |  |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 15 | `Archivoval` | nvarchar(50) | ANO | (suser_sname()) |  |
| 16 | `napln` | nvarchar(1000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_PredavaciProtokolPostuPol_ARCHIV_1` (CLUSTERED) — `ID`
