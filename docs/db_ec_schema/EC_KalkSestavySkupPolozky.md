# EC_KalkSestavySkupPolozky

**Schema**: dbo · **Cluster**: Production · **Rows**: 199 · **Size**: 0.13 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `ID_List` | int | ANO |  |  |
| 4 | `PoradiListu` | int | ANO |  |  |
| 5 | `ID_Skupiny` | int | ANO |  |  |
| 6 | `Poradi` | int | ANO |  |  |
| 7 | `Aktivni` | bit | NE | ((1)) |  |
| 8 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_KalkStandardPolozky` (CLUSTERED) — `ID`
