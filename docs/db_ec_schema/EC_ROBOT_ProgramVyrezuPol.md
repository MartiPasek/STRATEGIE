# EC_ROBOT_ProgramVyrezuPol

**Schema**: dbo · **Cluster**: Production · **Rows**: 2,285 · **Size**: 0.20 MB · **Sloupců**: 9 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Hlav` | int | NE |  |  |
| 3 | `Y_OrientaceNaStred` | bit | ANO |  |  |
| 4 | `Y_PosZleva` | numeric(5,1) | ANO |  |  |
| 5 | `X_PosVyska` | numeric(5,1) | NE |  |  |
| 6 | `X_OrientaceNa` | char(10) | ANO |  | H=Horni hrana,S=Stred komponenty, D=Dolni hrana  |
| 7 | `ID_Dilu` | int | ANO |  |  |
| 8 | `Pocet_Dilu` | tinyint | ANO |  |  |
| 9 | `Roztec_mezi_Dily` | numeric(5,1) | ANO |  |  |

## Cizí klíče (declared)

- `ID_Dilu` → [`EC_ROBOT_Dil`](EC_ROBOT_Dil.md).`ID` _(constraint: `FK_EC_ROBOT_ProgramVyrezuPol_EC_ROBOT_Dil`)_
- `ID_Hlav` → [`EC_ROBOT_ProgramVyrezuHlav`](EC_ROBOT_ProgramVyrezuHlav.md).`ID` _(constraint: `FK_EC_ROBOT_ProgramVyrezuPol_EC_ROBOT_ProgramVyrezuHlav`)_

## Indexy

- **PK** `PK_EC_ROBOT_ProgramVyrezuPol` (CLUSTERED) — `ID`
