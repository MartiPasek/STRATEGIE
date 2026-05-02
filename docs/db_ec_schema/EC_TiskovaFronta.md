# EC_TiskovaFronta

**Schema**: dbo · **Cluster**: Other · **Rows**: 89 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDFormulare` | int | ANO |  |  |
| 3 | `IDZdroj` | int | ANO |  |  |
| 4 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 5 | `Typ` | int | ANO |  |  |
| 6 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `Zpracovano` | bit | ANO | ((0)) |  |
| 9 | `IPTiskarny` | nvarchar(20) | ANO |  |  |

## Indexy

- **PK** `PK_EC_TiskovaFronta` (CLUSTERED) — `ID`
