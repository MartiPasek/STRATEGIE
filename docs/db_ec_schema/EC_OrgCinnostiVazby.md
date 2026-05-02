# EC_OrgCinnostiVazby

**Schema**: dbo · **Cluster**: HR · **Rows**: 15,979 · **Size**: 1.79 MB · **Sloupců**: 19 · **FK**: 6 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `OK` | bit | NE | ((1)) |  |
| 3 | `IDcinnost` | int | ANO |  |  |
| 4 | `IDTypText` | int | ANO |  |  |
| 5 | `IDpost` | int | ANO |  |  |
| 6 | `IDsmernice` | int | ANO |  |  |
| 7 | `CisloZam` | int | ANO |  |  |
| 8 | `CisloOrg` | int | ANO |  |  |
| 9 | `MiraZaskoleni` | tinyint | ANO |  |  |
| 10 | `VazbaTyp` | tinyint | NE |  |  |
| 11 | `VazbaPopis` | varchar(14) | NE |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
| 16 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 17 | `DatZamceni` | datetime | ANO |  |  |
| 18 | `ViewNumber` | int | ANO |  |  |
| 19 | `IDForm` | int | ANO |  |  |

## Cizí klíče (declared)

- `IDTypText` → [`EC_OrgCinnostiTypTexty`](EC_OrgCinnostiTypTexty.md).`ID` _(constraint: `FK_EC_OrgCinnostiVazby_EC_OrgCinnostiTypTexty`)_
- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_OrgCinnostiVazby_TabCisZam`)_
- `IDpost` → [`EC_OrgPost`](EC_OrgPost.md).`ID` _(constraint: `FK_EC_OrgCinnostiVazby_EC_OrgPost`)_
- `CisloOrg` → [`TabCisOrg`](TabCisOrg.md).`CisloOrg` _(constraint: `FK_EC_OrgCinnostiVazby_TabCisOrg`)_
- `IDcinnost` → [`EC_OrgCinnosti`](EC_OrgCinnosti.md).`ID` _(constraint: `FK_EC_OrgCinnostiVazby_EC_OrgCinnosti`)_
- `IDsmernice` → [`EC_OrgSmernice`](EC_OrgSmernice.md).`ID` _(constraint: `FK_EC_OrgCinnostiVazby_EC_OrgSmernice`)_

## Indexy

- **PK** `PK_EC_OrgCinnostiVazby` (CLUSTERED) — `ID`
