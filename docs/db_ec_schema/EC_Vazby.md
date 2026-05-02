# EC_Vazby

**Schema**: dbo · **Cluster**: Other · **Rows**: 95,512 · **Size**: 8.63 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDZdroj` | int | ANO |  |  |
| 3 | `IDCil` | int | ANO |  |  |
| 4 | `TypZdroj` | int | ANO |  |  |
| 5 | `TypCil` | int | ANO |  |  |
| 6 | `DelEnable` | bit | ANO | ((0)) |  |
| 7 | `IDVazbaZdroj` | int | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `Smazana` | bit | ANO | ((0)) |  |
| 13 | `DatZobrazeni` | datetime | ANO |  | Založeno pro zápis informace, kdy byl naposledy otevřen daný formulář pro daného uživatele. Vztaženo na práva (např. pro |

## Indexy

- **INDEX** `ClusteredIndex-20181019-120443` (CLUSTERED) — `IDCil, IDZdroj`
- **INDEX** `<Name of Missing Index, sysname,>` (NONCLUSTERED) — `ID, TypZdroj, TypCil`
