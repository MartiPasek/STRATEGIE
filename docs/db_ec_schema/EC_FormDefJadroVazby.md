# EC_FormDefJadroVazby

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 69 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE | ([dbo].[EC_GET_NewID_2]('EC_FormDefJadroVazby')) |  |
| 2 | `ID_MenuStrom` | int | ANO |  |  |
| 3 | `ID_JadroDetail` | int | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_FormDefJadroVazby` (CLUSTERED) — `ID`
