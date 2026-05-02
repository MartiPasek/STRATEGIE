# EC_DopravaZakaznikovi_DruhDopravy

**Schema**: dbo · **Cluster**: Other · **Rows**: 10 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(200) | ANO |  |  |
| 3 | `DnyPredDodanim` | int | ANO |  |  |
| 4 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `KontrolaVyplneniDatumu` | bit | ANO | ((1)) |  |
| 7 | `TiskText` | nvarchar(256) | ANO | ('') |  |
| 8 | `Poznamka` | nvarchar(500) | ANO |  |  |
