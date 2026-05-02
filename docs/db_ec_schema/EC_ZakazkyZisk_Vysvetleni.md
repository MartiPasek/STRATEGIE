# EC_ZakazkyZisk_Vysvetleni

**Schema**: dbo · **Cluster**: Finance · **Rows**: 497 · **Size**: 0.20 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 3 | `Typ` | int | ANO | ((0)) | 1 = VP, 2=Vyroba, 3=Obchod |
| 4 | `VysvetleniCislo` | int | ANO |  |  |
| 5 | `VysvetleniKomentar` | nvarchar(4000) | ANO |  |  |
| 6 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
