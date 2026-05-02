# EC_VydejAZmenNaSklad_Archiv

**Schema**: dbo · **Cluster**: Other · **Rows**: 5,586 · **Size**: 2.63 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPol` | int | ANO |  |  |
| 3 | `IDZbosklad` | int | ANO |  |  |
| 4 | `Cislozakazky` | nvarchar(15) | ANO |  |  |
| 5 | `MnozstviOBJ` | numeric(19,6) | ANO |  |  |
| 6 | `MnozstviVydej` | numeric(20,6) | ANO |  |  |
| 7 | `RegCis` | nvarchar(30) | ANO |  |  |
| 8 | `MJ` | nvarchar(10) | ANO |  |  |
| 9 | `Nazev1` | nvarchar(100) | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | ANO |  |  |
| 11 | `DatPorizeni` | datetime | ANO |  |  |
| 12 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 13 | `Archivoval` | nvarchar(128) | ANO | (suser_sname()) |  |
| 14 | `PoznamkaArchiv` | nvarchar(1000) | ANO |  |  |
