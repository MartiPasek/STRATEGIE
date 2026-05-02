# EC_Vytizeni_LogPlanSumaPol

**Schema**: dbo · **Cluster**: Production · **Rows**: 39,930,753 · **Size**: 6806.96 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `IDHlav` | int | NE |  |  |
| 2 | `ID` | int | NE |  |  |
| 3 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 4 | `Datum` | date | ANO |  |  |
| 5 | `PocetHodin` | int | ANO |  |  |
| 6 | `Autor` | nvarchar(126) | ANO |  |  |
| 7 | `DatPorizeni` | datetime | ANO |  |  |
| 8 | `Zmenil` | nvarchar(126) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 11 | `Typ` | int | ANO |  |  |
| 12 | `Blokovano` | bit | ANO |  |  |
| 13 | `Barva` | nvarchar(10) | ANO |  |  |
| 14 | `BarvaRamecek` | nvarchar(10) | ANO |  |  |
| 15 | `ZobrazujNuly` | bit | ANO |  |  |
| 16 | `JsemInstalace` | bit | ANO |  |  |
| 17 | `Externe` | bit | ANO |  |  |
