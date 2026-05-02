# EC_OrgCinnosti

**Schema**: dbo · **Cluster**: HR · **Rows**: 579 · **Size**: 0.26 MB · **Sloupců**: 21 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | NE | ((999)) |  |
| 3 | `Cinnost` | nvarchar(128) | NE | (N'Nepopsáno! Doplnit!') |  |
| 4 | `Poznamka` | nvarchar(255) | ANO |  |  |
| 5 | `SumPost` | int | ANO |  |  |
| 6 | `SumSmer` | int | ANO |  |  |
| 7 | `SumPred` | int | ANO |  |  |
| 8 | `SumPrav` | int | ANO |  |  |
| 9 | `SumZodp` | int | ANO |  |  |
| 10 | `SumSkup` | int | ANO |  |  |
| 11 | `SumPrio` | int | ANO |  |  |
| 12 | `SumZam` | int | ANO |  |  |
| 13 | `SumOrg` | int | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 18 | `DatZmeny` | datetime | ANO |  |  |
| 19 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 20 | `DatZamceni` | datetime | ANO |  |  |
| 22 | `Typ` | smallint | ANO |  |  |
| 23 | `TypText` | varchar(7) | NE |  |  |

## Cizí klíče (declared)

- `ID` → [`EC_OrgCinnosti`](EC_OrgCinnosti.md).`ID` _(constraint: `FK_EC_OrgCinnosti_EC_OrgCinnosti`)_

## Indexy

- **PK** `PK_EC_OrgPostCinnosti` (CLUSTERED) — `ID`
