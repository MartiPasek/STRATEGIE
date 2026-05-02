# EC_SvetlaVykonyPol

**Schema**: dbo · **Cluster**: Other · **Rows**: 695 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloSvetla` | int | NE |  |  |
| 3 | `Procento` | int | NE |  |  |
| 4 | `IDHlav` | int | NE |  |  |
| 5 | `IDSkupina` | int | ANO |  |  |
| 6 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 7 | `OdeslatDoPLC` | bit | ANO |  |  |
| 8 | `PlatnostOD` | datetime | ANO |  |  |
