# EC_KmenZbozi_Vlastnosti

**Schema**: dbo · **Cluster**: Production · **Rows**: 5 · **Size**: 0.08 MB · **Sloupců**: 11 · **FK**: 3 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDDefVlastnost` | int | ANO |  |  |
| 3 | `IDKmenZbozi` | int | ANO |  |  |
| 4 | `IDZboSklad` | int | ANO |  |  |
| 5 | `IDSkupina` | int | ANO |  |  |
| 6 | `Poradi` | int | ANO |  |  |
| 7 | `Poznamka` | ntext | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IDKmenZbozi` → `TabKmenZbozi`.`ID` _(constraint: `FK_EC_KmenZbozi_Vlastnosti_TabKmenZbozi`)_
- `IDZboSklad` → `TabStavSkladu`.`ID` _(constraint: `FK_EC_KmenZbozi_Vlastnosti_TabStavSkladu`)_
- `IDDefVlastnost` → [`EC_KmenZbozi_DefVlastnosti`](EC_KmenZbozi_DefVlastnosti.md).`ID` _(constraint: `FK_EC_KmenZbozi_Vlastnosti_EC_KmenZbozi_DefVlastnosti`)_

## Indexy

- **PK** `PK_EC_KmenZbozi_Vlastnosti` (CLUSTERED) — `ID`
