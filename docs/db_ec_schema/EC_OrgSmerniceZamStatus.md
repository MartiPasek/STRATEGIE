# EC_OrgSmerniceZamStatus

**Schema**: dbo · **Cluster**: HR · **Rows**: 179,540 · **Size**: 11.88 MB · **Sloupců**: 11 · **FK**: 2 · **Indexů**: 3

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Smernice` | int | NE |  |  |
| 3 | `CisloZam` | int | NE |  |  |
| 4 | `Podepsana` | bit | NE | ((0)) |  |
| 5 | `MiraZaskoleni` | tinyint | NE | ((100)) |  |
| 6 | `Log` | tinyint | NE | ((0)) |  |
| 7 | `LogText` | varchar(17) | ANO |  |  |
| 8 | `Poznamka` | nvarchar(40) | ANO |  |  |
| 9 | `DatDo` | datetime | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Cizí klíče (declared)

- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_OrgSmerniceZamStatus_TabCisZam`)_
- `ID_Smernice` → [`EC_OrgSmernice`](EC_OrgSmernice.md).`ID` _(constraint: `FK_EC_OrgSmerniceZamStatus_EC_OrgSmernice`)_

## Indexy

- **PK** `PK_EC_OrgSmernicePodepisovani` (CLUSTERED) — `ID`
- **INDEX** `ID_Smernice_CisloZam_Log` (NONCLUSTERED) — `ID_Smernice, CisloZam, Log`
- **INDEX** `ID_Smernice_CisloZam` (NONCLUSTERED) — `ID_Smernice, CisloZam`
