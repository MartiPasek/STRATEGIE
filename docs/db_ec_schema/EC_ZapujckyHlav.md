# EC_ZapujckyHlav

**Schema**: dbo · **Cluster**: Other · **Rows**: 27 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `PoradoveCislo` | int | ANO |  |  |
| 3 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 5 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 6 | `DatZmeny` | datetime | ANO |  |  |
| 7 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 8 | `CisloZakazky_Cil` | nvarchar(10) | ANO |  |  |
| 9 | `CisloZakazky_Zdroj` | nvarchar(10) | ANO |  |  |
