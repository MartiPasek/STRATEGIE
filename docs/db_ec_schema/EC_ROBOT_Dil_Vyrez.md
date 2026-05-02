# EC_ROBOT_Dil_Vyrez

**Schema**: dbo · **Cluster**: Production · **Rows**: 911 · **Size**: 0.13 MB · **Sloupců**: 10 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Dilu` | int | ANO |  |  |
| 3 | `TypVyrezu` | smallint | NE |  |  |
| 4 | `TypVyrezuT` | varchar(14) | NE |  | Jen pro obecnou informaci v editoru se pouzivaji texty z tabulky EC_ROBOT_TypVyrezu |
| 5 | `Je_stredem_dilu` | bit | ANO |  |  |
| 6 | `PoziceX_zdola` | numeric(5,1) | ANO |  |  |
| 7 | `PoziceY_zleva` | numeric(5,1) | ANO |  |  |
| 8 | `Velikost_X` | numeric(5,1) | ANO |  |  |
| 9 | `Velikost_Y` | numeric(5,1) | ANO |  |  |
| 10 | `ReadOnly` | bit | ANO |  |  |

## Cizí klíče (declared)

- `ID_Dilu` → [`EC_ROBOT_Dil`](EC_ROBOT_Dil.md).`ID` _(constraint: `FK_EC_ROBOT_Dil_Vyrez_EC_ROBOT_Dil`)_

## Indexy

- **PK** `PK_EC_ROBOT_Vyrez` (CLUSTERED) — `ID`
