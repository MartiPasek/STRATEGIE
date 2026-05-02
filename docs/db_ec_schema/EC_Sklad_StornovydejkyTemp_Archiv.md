# EC_Sklad_StornovydejkyTemp_Archiv

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Poradi` | int | ANO |  |  |
| 3 | `RegCis` | nvarchar(30) | ANO |  |  |
| 4 | `Nazev1` | nvarchar(100) | ANO |  |  |
| 5 | `Poznamka` | ntext | ANO |  |  |
| 6 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 7 | `MnozstviPuvodni` | numeric(19,6) | ANO |  |  |
| 8 | `MnozstviVracene` | numeric(19,6) | ANO |  |  |
| 9 | `StavSkladu` | numeric(19,6) | ANO |  |  |
| 10 | `MJ` | nvarchar(10) | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | ANO |  |  |
| 12 | `DatPorizeni` | datetime | ANO |  |  |
| 13 | `Umisteni` | nvarchar(15) | ANO |  |  |
| 14 | `nezobrazuj` | bit | ANO |  |  |
| 15 | `SV_ID` | int | ANO |  |  |
| 16 | `MnozstviStornoVydej` | numeric(19,6) | ANO |  |  |
| 17 | `Autor_Ulozil` | nvarchar(128) | ANO | (suser_name()) |  |
| 18 | `DatPorizeni_Ulozil` | datetime | ANO | (getdate()) |  |
