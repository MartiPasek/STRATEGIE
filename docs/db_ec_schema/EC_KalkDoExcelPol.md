# EC_KalkDoExcelPol

**Schema**: dbo · **Cluster**: Production · **Rows**: 780 · **Size**: 0.33 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `IDHlav` | int | ANO |  |  |
| 2 | `ExcelNazevListu` | varchar(9) | NE |  |  |
| 3 | `Skupina` | int | ANO |  |  |
| 4 | `Bezeichnung` | nvarchar(160) | ANO |  |  |
| 5 | `RegCis` | nvarchar(30) | ANO |  |  |
| 6 | `Vyrobce` | nvarchar(50) | ANO |  |  |
| 7 | `PocetKusu` | numeric(12,2) | ANO |  |  |
| 8 | `KalkCena` | numeric(18,6) | ANO |  |  |
| 9 | `RabatP` | numeric(7,2) | ANO |  |  |
| 10 | `RabatN` | numeric(7,2) | ANO |  |  |
| 11 | `K_ARB` | numeric(5,2) | ANO |  |  |
| 12 | `K_VKM` | numeric(5,2) | ANO |  |  |
| 13 | `PoznamkaVP` | nvarchar(128) | ANO |  |  |
| 14 | `PoznamkaNakup` | nvarchar(128) | ANO |  |  |
| 15 | `Hmotnost` | numeric(19,6) | ANO |  |  |
| 16 | `_ExcelColor` | nvarchar(4000) | ANO |  |  |
| 17 | `_ExcelComment` | nvarchar(4000) | ANO |  |  |
