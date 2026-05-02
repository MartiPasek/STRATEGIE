# EC_Ukoly_SeznamResitelu

**Schema**: dbo · **Cluster**: Other · **Rows**: 165 · **Size**: 0.20 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKontroly` | int | ANO |  |  |
| 3 | `IDDefUkolu` | int | ANO |  |  |
| 4 | `IDOpakUkolu` | int | ANO |  |  |
| 5 | `CisloZam` | int | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `Kopie` | bit | ANO | ((0)) |  |
| 10 | `NeaktivniOD` | datetime | ANO |  |  |
| 11 | `NeaktivniDO` | datetime | ANO |  |  |
| 12 | `Neaktivni` | int | NE |  |  |

## Indexy

- **PK** `PK_EC_Ukoly_SeznamResitelu` (CLUSTERED) — `ID`
