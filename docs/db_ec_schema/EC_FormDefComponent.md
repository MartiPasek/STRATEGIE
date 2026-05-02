# EC_FormDefComponent

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 37 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Druh` | int | ANO |  |  |
| 3 | `Typ` | int | NE |  |  |
| 4 | `Name` | nvarchar(40) | ANO |  |  |
| 5 | `Popis` | nvarchar(100) | ANO |  |  |
| 6 | `PoradiCreate` | int | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `FMX` | tinyint | ANO | ((1)) | 1 = VLC, 2 = FMX |

## Cizí klíče (declared)

- `ID` → [`EC_FormDefComponent`](EC_FormDefComponent.md).`ID` _(constraint: `FK_EC_FormDefComponent_EC_FormDefComponent`)_
- `ID` → [`EC_FormDefComponent`](EC_FormDefComponent.md).`ID` _(constraint: `FK_EC_FormDefComponent_EC_FormDefComponent1`)_

## Indexy

- **PK** `PK_EC_FormDefComponent` (CLUSTERED) — `ID`
