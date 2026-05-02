# EC_Kalkulace_ZalozeniCenyHlav

**Schema**: dbo · **Cluster**: Production · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 3 | `CisloDodavatel` | int | ANO |  |  |
| 4 | `RabatN` | int | ANO |  |  |
| 5 | `Mena` | nvarchar(3) | ANO |  |  |
| 6 | `CisloNabidky` | nvarchar(100) | ANO |  |  |
| 7 | `PoznamkaCenik` | nvarchar(1000) | ANO |  |  |
| 8 | `PlatnostOd` | date | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 11 | `OblastCeny` | int | ANO |  | 1 = Projektová, 2 = Pro zákazníka, 3 = Pro všechny  |
| 12 | `DruhZadaneCeny` | int | ANO |  |  |
