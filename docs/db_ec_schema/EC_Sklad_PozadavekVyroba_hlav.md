# EC_Sklad_PozadavekVyroba_hlav

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 19 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 3 | `DatZpracovani` | datetime | ANO |  |  |
| 4 | `Zpracoval` | nvarchar(126) | ANO |  |  |
| 5 | `Priorita` | int | ANO | ((1)) |  |
| 6 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `DatOdeslani` | datetime | ANO |  |  |
| 9 | `CisloZakazkyVzor` | nvarchar(10) | ANO |  |  |
| 10 | `Urgentni` | bit | ANO | ((0)) |  |
| 11 | `Typ` | int | ANO | ((0)) | 0 = vyroba zadání, 1 = určeno pro Sklad VKM, 2 = určeno pro s1 sklad  |
| 12 | `IDOldPozadavek` | int | ANO |  |  |
| 13 | `VeZpracovani` | bit | ANO | ((0)) |  |
| 14 | `Resitel` | int | ANO |  |  |
| 15 | `Color` | smallint | ANO |  |  |
| 16 | `VydanPredOdeslanim` | bit | ANO |  |  |
| 17 | `DatStorna` | datetime | ANO |  |  |
| 18 | `Stornoval` | nvarchar(126) | ANO |  |  |
| 19 | `Poznamka` | nvarchar(1000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Sklad_PozadavekVyroba` (CLUSTERED) — `ID`
