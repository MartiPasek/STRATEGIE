# EC_ES_Cestaky

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `DUZP` | datetime | ANO |  |  |
| 4 | `Castka` | numeric(18,2) | ANO |  |  |
| 5 | `Mena` | nvarchar(3) | ANO |  |  |
| 6 | `CisloZakazky` | nvarchar(50) | ANO |  |  |
| 7 | `Poznamka` | nvarchar(250) | ANO |  |  |
| 8 | `DatPorizeni` | datetime | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_ES_Cestaky` (CLUSTERED) — `ID`
