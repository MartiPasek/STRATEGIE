# EC_MenuStrom_Historie

**Schema**: dbo · **Cluster**: Other · **Rows**: 10,277 · **Size**: 1.71 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `AppGUID` | uniqueidentifier | NE |  |  |
| 3 | `Typ` | nvarchar(20) | ANO |  |  |
| 4 | `Soudecek` | int | ANO |  |  |
| 5 | `Aktivni` | bit | NE | ((1)) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `CisloZalozky` | int | ANO |  |  |
| 11 | `AktZalozkaSoudecek` | bit | ANO | ((0)) |  |
| 12 | `DevPoznamka` | nvarchar(80) | ANO |  |  |
| 13 | `FilterJmeno` | nvarchar(50) | ANO |  |  |
| 14 | `FilterHodnota` | nvarchar(50) | ANO |  |  |

## Indexy

- **PK** `PK_EC_MenuStrom_Historie` (CLUSTERED) — `ID`
