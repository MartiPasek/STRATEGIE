# EC_ROBOT_FrezovaniVyrezy

**Schema**: dbo · **Cluster**: Production · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 24 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(50) | ANO |  |  |
| 3 | `CisloDveri` | int | ANO |  |  |
| 4 | `NazevDveri` | nvarchar(30) | ANO |  |  |
| 5 | `PopisDveri` | nvarchar(50) | ANO |  |  |
| 6 | `CistaVyskaDveri` | smallint | ANO |  |  |
| 7 | `CistaSirkaDveri` | smallint | ANO |  |  |
| 8 | `TypVyrezu` | int | ANO |  |  |
| 9 | `Vyrez_Pos_X` | numeric(5,1) | ANO |  |  |
| 10 | `Vyrez_Pos_Y` | numeric(5,1) | ANO |  |  |
| 11 | `Vyrez_Vyska_X` | numeric(5,1) | ANO |  |  |
| 12 | `Vyrez_Sirka_Y` | numeric(5,1) | ANO |  |  |
| 13 | `PopisDilu` | nvarchar(50) | ANO |  |  |
| 14 | `CisloDilu` | int | ANO |  |  |
| 15 | `Dil_Pos_X` | numeric(5,1) | ANO |  |  |
| 16 | `Dil_Pos_Y` | numeric(5,1) | ANO |  |  |
| 17 | `Dil_Vyska_X` | numeric(5,1) | ANO |  |  |
| 18 | `Dil_Sirka_Y` | numeric(5,1) | ANO |  |  |
| 19 | `DilPoznamka` | nvarchar(50) | ANO |  |  |
| 20 | `ID_Pol` | int | ANO |  |  |
| 21 | `ID_Hlav` | int | ANO |  |  |
| 22 | `Datum_generovani` | datetime | NE | (getdate()) |  |
| 23 | `Stav` | smallint | ANO |  |  |
| 24 | `PorCisNastroje` | smallint | ANO |  |  |

## Indexy

- **PK** `PK_EC_ROBOT_FrezovaniVyrezy` (CLUSTERED) — `ID`
