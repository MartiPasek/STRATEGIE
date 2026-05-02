# EC_Vytizeni_LogZakazkyHlav

**Schema**: dbo · **Cluster**: Production · **Rows**: 7,723 · **Size**: 1.13 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Poznamka` | nvarchar(2000) | ANO |  |  |
| 5 | `Procedura` | nvarchar(100) | ANO |  |  |
| 6 | `PocetPolozek` | int | ANO |  |  |
| 7 | `FiltrVP` | nvarchar(300) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_LogZakazkyHlav` (CLUSTERED) — `ID`
