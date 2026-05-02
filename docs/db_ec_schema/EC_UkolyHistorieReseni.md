# EC_UkolyHistorieReseni

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,825,545 · **Size**: 230.73 MB · **Sloupců**: 12 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDUkol` | int | NE |  |  |
| 3 | `CisloZam` | int | NE |  |  |
| 4 | `Aktivita` | tinyint | NE |  |  |
| 5 | `AktivitaText` | varchar(26) | NE |  |  |
| 6 | `Hodiny` | numeric(19,2) | NE | ((0)) |  |
| 7 | `Priorita` | int | ANO |  |  |
| 8 | `Komentar` | nvarchar(MAX) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IDUkol` → [`EC_Ukoly`](EC_Ukoly.md).`ID` _(constraint: `FK_EC_UkolyHistorieReseni_EC_Ukoly`)_

## Indexy

- **PK** `PK_EC_UkolyHistorieReseni` (CLUSTERED) — `ID`
