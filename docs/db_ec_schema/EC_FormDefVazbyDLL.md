# EC_FormDefVazbyDLL

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 17 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | ANO |  |  |
| 3 | `Nazev` | nvarchar(255) | ANO |  |  |
| 4 | `KodFormulare` | int | ANO |  |  |
| 5 | `Tag` | int | ANO |  |  |
| 6 | `CisloPrehledu` | int | ANO |  |  |
| 7 | `TypDokladu` | nvarchar(25) | ANO |  |  |
| 8 | `Poznamka` | ntext | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_FormDefVazbyDLL` (CLUSTERED) — `ID`
