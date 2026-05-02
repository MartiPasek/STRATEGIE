# EC_OrgSmernice

**Schema**: dbo · **Cluster**: HR · **Rows**: 1,439 · **Size**: 3.48 MB · **Sloupců**: 36 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | ANO |  |  |
| 3 | `Typ` | tinyint | NE | ((0)) |  |
| 4 | `TypText` | varchar(10) | NE |  |  |
| 5 | `UzivTyp` | tinyint | NE | ((0)) |  |
| 6 | `UzivTypText` | varchar(9) | NE |  |  |
| 7 | `Nazev` | nvarchar(255) | ANO | (N'NOVÁ') |  |
| 8 | `Popis` | ntext | ANO | (N'NOVÁ') |  |
| 9 | `Priorita` | int | ANO |  |  |
| 10 | `PlatnostOd` | datetime | ANO |  |  |
| 11 | `PlatnostDo` | datetime | ANO |  |  |
| 12 | `Status` | tinyint | NE | ((0)) |  |
| 13 | `StatusText` | varchar(25) | ANO |  |  |
| 14 | `Aktivni` | int | NE |  |  |
| 15 | `Verze` | smallint | NE | ((1)) |  |
| 16 | `VerzePoznamka` | nvarchar(255) | ANO |  |  |
| 17 | `ID_Orig` | int | ANO |  |  |
| 18 | `Archiv` | int | NE |  |  |
| 19 | `SumVazebNaCinnosti` | int | ANO |  |  |
| 20 | `Pristupnost` | tinyint | NE | ((0)) |  |
| 21 | `PristupnostText` | varchar(7) | ANO |  |  |
| 22 | `Urceni` | tinyint | ANO |  |  |
| 23 | `UrceniText` | varchar(18) | ANO |  |  |
| 24 | `Aktivoval` | nvarchar(128) | ANO |  |  |
| 25 | `DatAktivace` | datetime | ANO |  |  |
| 26 | `IDKvalif` | int | ANO |  |  |
| 27 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 28 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 29 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 30 | `DatZmeny` | datetime | ANO |  |  |
| 31 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 32 | `DatZamceni` | datetime | ANO |  |  |
| 33 | `DatPorizeni_X` | datetime | ANO |  |  |
| 34 | `CisloOrg` | int | ANO |  |  |
| 35 | `IDSkoleni` | int | ANO |  |  |
| 38 | `AutorSmernice` | int | ANO |  |  |

## Cizí klíče (declared)

- `ID` → [`EC_OrgSmernice`](EC_OrgSmernice.md).`ID` _(constraint: `FK_EC_OrgSmernice_EC_OrgSmernice`)_

## Indexy

- **PK** `PK_EC_Smernice` (CLUSTERED) — `ID`
