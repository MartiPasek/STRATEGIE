# EC_PredavaciProtokolPostuPol

**Schema**: dbo · **Cluster**: Production · **Rows**: 3,613 · **Size**: 1.62 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `IDCinnost` | int | ANO |  |  |
| 4 | `CisloPostu` | int | ANO |  |  |
| 5 | `NazevPostu` | nvarchar(100) | ANO |  |  |
| 6 | `Poradi` | int | ANO | ((1)) |  |
| 7 | `Cinnost` | nvarchar(200) | ANO |  |  |
| 8 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 9 | `PredanoProcent` | numeric(18,0) | ANO | ((0)) |  |
| 10 | `DatPodpisuPredavajiciho` | datetime | ANO |  |  |
| 11 | `DatPodpisuPrebirajiciho` | datetime | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
| 16 | `Napln` | nvarchar(1000) | ANO |  |  |
| 17 | `IDKvalifikace` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_PredavaciProtokolPostuPol_1` (CLUSTERED) — `ID`
