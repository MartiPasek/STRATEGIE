# EC_ZakazkyHodnoceni

**Schema**: dbo · **Cluster**: Finance · **Rows**: 49,262 · **Size**: 4.81 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 3 | `IDPredlohy` | int | ANO |  |  |
| 4 | `Hodnoceni` | int | ANO |  |  |
| 5 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `TypHodnoceni` | smallint | ANO |  | Od koho je hodnoceni: 1 = sefmonter, 2= vedouci vyroby , 3 = vedoucí projektu |
