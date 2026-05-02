# EC_SeznamHW

**Schema**: dbo · **Cluster**: Other · **Rows**: 51 · **Size**: 0.09 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDNadrazene` | int | ANO |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `Zarizeni` | nvarchar(50) | NE |  |  |
| 5 | `Vyrobce` | nvarchar(50) | NE |  |  |
| 6 | `Typ` | nvarchar(50) | NE |  |  |
| 7 | `Umisteni` | nvarchar(100) | NE |  |  |
| 8 | `MACadr` | nvarchar(50) | ANO |  |  |
| 9 | `IPadr` | nvarchar(15) | ANO |  |  |
| 10 | `Ovladace` | ntext | ANO |  |  |
| 11 | `ZalohaDalsi` | datetime | ANO |  |  |
| 12 | `ZalohaPosedni` | datetime | ANO |  |  |
| 13 | `Informace` | ntext | ANO |  |  |

## Indexy

- **PK** `PK_EC_SeznamHW` (CLUSTERED) — `ID`
