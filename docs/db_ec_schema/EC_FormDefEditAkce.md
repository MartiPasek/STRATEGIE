# EC_FormDefEditAkce

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 4,756 · **Size**: 3.01 MB · **Sloupců**: 27 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE | ([dbo].[EC_GET_NewID_2]('EC_FormDefEditAkce')) |  |
| 2 | `ID_Form` | int | ANO |  |  |
| 3 | `ID_Komponenty` | int | ANO |  |  |
| 4 | `ID_PopupMenu` | int | ANO |  |  |
| 5 | `ID_Soudecku` | int | ANO |  |  |
| 6 | `ID_Formulare` | int | ANO |  |  |
| 7 | `ID_Prehledu` | int | ANO |  |  |
| 8 | `Typ` | nvarchar(128) | NE | ('Default') |  |
| 9 | `CisloAkce` | int | NE |  |  |
| 10 | `Poradi` | int | NE | ((1)) |  |
| 11 | `Parametr1` | int | ANO |  |  |
| 12 | `Parametr2` | nvarchar(255) | ANO | ('') |  |
| 13 | `Parametr3` | nvarchar(255) | ANO |  |  |
| 14 | `Parametr4` | nvarchar(255) | ANO |  |  |
| 15 | `ReturnValues` | nvarchar(255) | ANO |  | Navratove hodnoty Akce (uloyeni napr. do SQLite AppVar) |
| 16 | `ParametrSqlIf` | nvarchar(255) | ANO |  |  |
| 17 | `ReakceNaRLO` | nvarchar(1) | ANO |  |  |
| 18 | `SqlIf` | ntext | ANO |  |  |
| 19 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 20 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 21 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 22 | `DatZmeny` | datetime | ANO |  |  |
| 23 | `Typ2` | nvarchar(128) | NE | ('Default') |  |
| 24 | `FMX` | tinyint | ANO | ((1)) | 1 = VLC, 2 = FMX |
| 25 | `CitacSpusteni` | int | ANO |  |  |
| 26 | `NaposledySpusteno` | datetime | ANO |  |  |
| 27 | `PoprveSpusteno` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `ID_Form` → [`EC_FormDef`](EC_FormDef.md).`ID` _(constraint: `FK_EC_FormDefEditAkce_EC_FormDef`)_
- `ID_PopupMenu` → [`EC_FormDefPopupMenu`](EC_FormDefPopupMenu.md).`ID` _(constraint: `FK_EC_FormDefEditAkce_EC_FormDefPopupMenu`)_

## Indexy

- **PK** `PK_EC_FormDefEditAkce` (CLUSTERED) — `ID`
