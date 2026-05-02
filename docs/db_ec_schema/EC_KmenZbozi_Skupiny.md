# EC_KmenZbozi_Skupiny

**Schema**: dbo · **Cluster**: Production · **Rows**: 4 · **Size**: 0.09 MB · **Sloupců**: 10 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(255) | ANO |  |  |
| 3 | `Popis` | ntext | ANO |  |  |
| 4 | `IDNadrazene` | int | ANO |  |  |
| 5 | `IDKmenZbozi` | int | ANO |  |  |
| 6 | `Poznamka` | ntext | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IDKmenZbozi` → `TabKmenZbozi`.`ID` _(constraint: `FK_EC_KmenZbozi_Skupiny_TabKmenZbozi`)_

## Indexy

- **PK** `PK_EC_KmenZbozi_Skupiny` (CLUSTERED) — `ID`
