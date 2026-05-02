# EC_ZakazkyHodnoceniPredlohy

**Schema**: dbo · **Cluster**: Finance · **Rows**: 19 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `RozmeziMin` | int | ANO |  |  |
| 4 | `RozmeziMax` | int | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `TypPredlohy` | smallint | NE |  | Komu zobrazovat: 1 = sefmonter, 2 = vedouci vyroby, 3 = Vedoucí projektu |
| 8 | `DefaultniHodnota` | int | ANO |  |  |
