# EC_ROBOT_ProgramVyrezuHlav

**Schema**: dbo · **Cluster**: Production · **Rows**: 772 · **Size**: 0.13 MB · **Sloupců**: 6 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(15) | NE |  |  |
| 3 | `CisloDveri` | smallint | ANO |  |  |
| 4 | `ID_Dveri` | int | ANO |  |  |
| 5 | `Popis` | nvarchar(30) | ANO |  |  |
| 6 | `KotovanoShora` | bit | ANO |  |  |

## Cizí klíče (declared)

- `ID_Dveri` → [`EC_ROBOT_Dvere`](EC_ROBOT_Dvere.md).`ID` _(constraint: `FK_EC_ROBOT_ProgramVyrezuHlav_EC_ROBOT_Dvere`)_
- `CisloZakazky` → `TabZakazka`.`CisloZakazky` _(constraint: `FK_EC_ROBOT_ProgramVyrezuHlav_EC_ROBOT_ProgramVyrezuHlav`)_

## Indexy

- **PK** `PK_EC_ROBOT_ProgramVyrezu` (CLUSTERED) — `ID`
