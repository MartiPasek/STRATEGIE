# EC_Vytizeni_Historie

**Schema**: dbo · **Cluster**: Production · **Rows**: 263 · **Size**: 0.20 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Rok` | int | NE |  |  |
| 2 | `Mesic` | int | NE |  |  |
| 3 | `Datum` | date | NE |  |  |
| 4 | `IDHlavLogu` | int | ANO |  |  |
| 5 | `HodinyMinRok` | decimal(18,2) | ANO |  |  |
| 6 | `HodinyBezNabMinRok` | decimal(18,2) | ANO |  |  |
| 7 | `Kapacita` | decimal(18,2) | ANO |  |  |
| 8 | `KapacitaDen` | decimal(18,2) | ANO |  |  |
| 9 | `HodinyRok` | decimal(18,2) | ANO |  |  |
| 10 | `HodinyRokBezNab` | decimal(18,2) | ANO |  |  |
| 11 | `VytvorenoUTC` | datetime2 | NE | (sysutcdatetime()) |  |
| 12 | `ID` | int | NE |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_Historie_1` (CLUSTERED) — `ID`
