# EC_OrgKvalifOtazky

**Schema**: dbo · **Cluster**: HR · **Rows**: 2,382 · **Size**: 0.40 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Text` | nvarchar(350) | ANO |  |  |
| 3 | `Typ` | int | ANO |  |  |
| 5 | `ID_Nadr` | int | ANO |  |  |
| 6 | `ID_Zdroj` | int | ANO |  |  |
| 7 | `ID_Cil` | int | ANO |  |  |
| 8 | `IDSkupHodnoceni` | int | ANO |  |  |
| 9 | `OdpovedTyp` | int | ANO |  |  |
| 10 | `Poradi` | int | ANO |  |  |
| 11 | `Aktivni` | bit | NE | ((0)) |  |
| 12 | `Hodnota` | smallint | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |
| 17 | `SpravnaOdpoved` | bit | ANO | ((0)) |  |
| 21 | `TypText` | varchar(23) | NE |  |  |

## Indexy

- **PK** `PK_EC_OrgKvalifOtazky` (CLUSTERED) — `ID`
