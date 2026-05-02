# EC_Dochazka_ChybyVDochazce_hlav

**Schema**: dbo · **Cluster**: HR · **Rows**: 2,819 · **Size**: 0.59 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 3 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 4 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 5 | `DatumPripaduOd` | datetime | ANO |  |  |
| 6 | `DatumPripaduDo` | datetime | ANO |  |  |
| 7 | `SpustenoRucne` | bit | ANO | ((0)) |  |
| 8 | `IDSkupiny` | int | ANO |  |  |
