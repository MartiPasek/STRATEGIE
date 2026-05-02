# EC_3Dtisk_fronta

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDModel` | int | NE |  |  |
| 3 | `IDMaterial1` | int | ANO |  |  |
| 4 | `IDMaterial2` | int | ANO |  |  |
| 5 | `IDMaterial3` | int | ANO |  |  |
| 6 | `IDMaterial4` | int | ANO |  |  |
| 7 | `Material1Mnoz` | int | ANO |  |  |
| 8 | `Material2Mnoz` | int | ANO |  |  |
| 9 | `Material3Mnoz` | int | ANO |  |  |
| 10 | `Material4Mnoz` | int | ANO |  |  |
| 11 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 12 | `PozadDatum` | datetime | ANO |  |  |
| 13 | `RealDatum` | datetime | ANO |  |  |
| 14 | `CasTiskKIS` | time | ANO |  |  |
| 15 | `CasTiskReal` | time | ANO |  |  |
| 16 | `Stav` | nvarchar(20) | NE | (N'wait') |  |
| 17 | `Priorita` | nvarchar(20) | ANO |  |  |
| 18 | `ProKoho` | int | NE |  |  |
| 19 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 20 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_3Dtisk_fronta` (CLUSTERED) — `ID`
