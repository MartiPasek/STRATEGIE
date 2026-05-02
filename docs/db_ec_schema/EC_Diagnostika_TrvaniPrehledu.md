# EC_Diagnostika_TrvaniPrehledu

**Schema**: dbo · **Cluster**: Logging · **Rows**: 342 · **Size**: 0.25 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloPrehledu` | int | NE |  |  |
| 3 | `Nazev` | nvarchar(50) | NE |  |  |
| 4 | `CelkoveSekundy` | int | NE |  |  |
| 5 | `PocetPristupu` | int | NE |  |  |
| 6 | `PrumerCas` | int | NE |  |  |
| 7 | `TydenCas` | int | NE |  |  |
| 8 | `TydenPoc` | int | NE |  |  |
| 9 | `TydenPrum` | int | NE |  |  |
| 10 | `MesicCas` | int | ANO |  |  |
| 11 | `MesicPoc` | int | ANO |  |  |
| 12 | `MesicPrum` | int | ANO |  |  |
| 13 | `NarustPrumeru` | float | ANO |  |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Diagnostika_TrvaniPrehledu` (CLUSTERED) — `ID`
