# EC_OrgPostKlobouk

**Schema**: dbo · **Cluster**: HR · **Rows**: 44 · **Size**: 0.20 MB · **Sloupců**: 16 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Post` | int | NE |  |  |
| 4 | `Nazev` | nvarchar(255) | ANO |  |  |
| 5 | `A1_UcelFirmy` | ntext | ANO |  |  |
| 6 | `A2_UcelPracovniPozice` | ntext | ANO |  |  |
| 7 | `B1_Umisteni` | ntext | ANO |  |  |
| 8 | `B2_Predpoklady` | ntext | ANO |  |  |
| 9 | `B3_Pravomoci` | ntext | ANO |  |  |
| 10 | `B4_Zodpovednosti` | ntext | ANO |  |  |
| 11 | `Poznamka` | ntext | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
| 16 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 17 | `DatZamceni` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `ID_Post` → [`EC_OrgPost`](EC_OrgPost.md).`ID` _(constraint: `FK_EC_OrgPostKlobouk_EC_OrgPost`)_

## Indexy

- **PK** `PK_EC_OrgPostKlobouk` (CLUSTERED) — `ID`
