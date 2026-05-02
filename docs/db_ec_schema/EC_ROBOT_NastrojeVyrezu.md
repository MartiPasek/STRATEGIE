# EC_ROBOT_NastrojeVyrezu

**Schema**: dbo · **Cluster**: Production · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_TypVyrezu` | int | NE |  |  |
| 3 | `Poradi` | tinyint | NE |  |  |
| 4 | `Nastroj` | tinyint | NE |  |  |
| 5 | `Prumer` | numeric(4,2) | NE |  |  |
| 6 | `Rychlost_mm_min` | smallint | NE |  |  |
| 7 | `Otacky_ot_min` | smallint | NE |  |  |
| 8 | `Popis` | nchar(30) | NE |  |  |

## Cizí klíče (declared)

- `ID` → [`EC_ROBOT_NastrojeVyrezu`](EC_ROBOT_NastrojeVyrezu.md).`ID` _(constraint: `FK_EC_ROBOT_NastrojeVyrezu_EC_ROBOT_NastrojeVyrezu`)_
- `ID_TypVyrezu` → [`EC_ROBOT_TypVyrezu`](EC_ROBOT_TypVyrezu.md).`ID` _(constraint: `FK_EC_ROBOT_NastrojeVyrezu_EC_ROBOT_TypVyrezu`)_

## Indexy

- **PK** `PK_EC_ROBOT_NastrojeVyrezu` (CLUSTERED) — `ID`
