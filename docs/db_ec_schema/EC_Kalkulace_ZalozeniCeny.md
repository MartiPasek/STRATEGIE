# EC_Kalkulace_ZalozeniCeny

**Schema**: dbo · **Cluster**: Production · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `RegCisKalk` | nvarchar(30) | ANO |  |  |
| 3 | `Bezeichnung` | nvarchar(160) | ANO |  |  |
| 4 | `Einheitpreis` | numeric(24,10) | ANO |  |  |
| 5 | `RabatN` | int | ANO |  |  |
| 6 | `CenaL` | numeric(18,2) | ANO |  |  |
| 7 | `CenaN` | numeric(18,2) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `CenaLCenik` | numeric(18,2) | ANO |  |  |
| 11 | `CenaNCenik` | numeric(18,2) | ANO |  |  |
| 12 | `RabatNCenik` | numeric(18,2) | ANO |  |  |
