# EC_TiskRadyDok

**Schema**: dbo · **Cluster**: Other · **Rows**: 15 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `RadaDokladu` | nvarchar(3) | ANO |  |  |
| 3 | `IDFormDef` | int | ANO |  |  |
| 4 | `Jazyk` | nvarchar(3) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `IDJadro` | int | ANO |  |  |

## Cizí klíče (declared)

- `IDFormDef` → `TabFormDef`.`ID` _(constraint: `FK_EC_TiskoveSestavy_TabFormDef`)_

## Indexy

- **PK** `PK_EC_TiskoveSestavy` (CLUSTERED) — `ID`
