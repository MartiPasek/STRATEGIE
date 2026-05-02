# EC_OrgPostZam

**Schema**: dbo · **Cluster**: HR · **Rows**: 465 · **Size**: 0.13 MB · **Sloupců**: 20 · **FK**: 3 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `ID_Post` | int | NE |  |  |
| 4 | `Zastupce1` | bit | NE | ((0)) |  |
| 5 | `Zastupce2` | bit | NE | ((0)) |  |
| 6 | `Potencialni` | bit | NE | ((0)) |  |
| 7 | `Aktivni` | bit | ANO |  |  |
| 8 | `Poznamka` | nvarchar(255) | ANO | ('') |  |
| 9 | `PlatnostOd` | datetime | ANO |  |  |
| 10 | `PlatnostDo` | datetime | ANO |  |  |
| 11 | `StupenZaskoleni` | tinyint | ANO |  |  |
| 12 | `StupenProdukce` | tinyint | ANO |  |  |
| 13 | `JmenoZam` | nvarchar(50) | ANO |  |  |
| 14 | `NazevPostu` | nvarchar(255) | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 18 | `DatZmeny` | datetime | ANO |  |  |
| 19 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 20 | `DatZamceni` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `ID_Post` → [`EC_OrgPost`](EC_OrgPost.md).`ID` _(constraint: `FK_EC_OrgPostZam_EC_OrgPost`)_
- `ID` → [`EC_OrgPostZam`](EC_OrgPostZam.md).`ID` _(constraint: `FK_EC_OrgPostZam_EC_OrgPostZam`)_
- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_OrgPostZam_TabCisZam`)_

## Indexy

- **PK** `PK_EC_OrgPostZam` (CLUSTERED) — `ID`
