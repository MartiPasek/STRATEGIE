# EC_Vyrobci_Smazat nepouziva se

**Schema**: dbo · **Cluster**: Production · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Zkratka` | nvarchar(5) | NE |  |  |
| 3 | `Nazev` | nvarchar(40) | NE | ('') |  |
| 4 | `Poznamka` | nvarchar(180) | ANO |  |  |
| 5 | `Blokovano` | bit | NE | ((0)) |  |
| 6 | `TvarRegCis` | nvarchar(80) | ANO |  |  |
| 7 | `Priklad01` | nvarchar(30) | ANO |  |  |
| 8 | `Priklad02` | nvarchar(30) | ANO |  |  |
| 9 | `Priklad03` | nvarchar(30) | ANO |  |  |
| 10 | `Priklad04` | nvarchar(30) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vyrobci` (CLUSTERED) — `ID`
