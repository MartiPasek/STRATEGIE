# EC_Banka_ParovaniVypisu

**Schema**: dbo · **Cluster**: Finance · **Rows**: 40 · **Size**: 0.07 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDBankSpoj` | int | ANO |  |  |
| 3 | `Mena` | nvarchar(3) | ANO |  |  |
| 4 | `KodBanky` | nvarchar(15) | ANO | ('') |  |
| 5 | `CisloUctu` | nvarchar(40) | ANO | ('') |  |
| 6 | `Aktivni` | bit | ANO |  |  |
| 7 | `IDTyp` | int | ANO |  |  |
| 8 | `PopisTransakce` | nvarchar(350) | ANO |  |  |
| 9 | `PopisBV` | nvarchar(35) | ANO |  |  |
| 10 | `TypTransakce` | nvarchar(35) | ANO |  |  |
| 11 | `SS` | nvarchar(10) | ANO |  |  |
| 12 | `KS` | nvarchar(10) | ANO |  |  |
| 13 | `VS` | nvarchar(20) | ANO |  |  |
| 14 | `CastkaOd` | numeric(18,6) | ANO |  |  |
| 15 | `CastkaDo` | numeric(18,6) | ANO |  |  |
| 16 | `KreditDebet` | tinyint | ANO |  |  |
| 17 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 18 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 19 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 20 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Banka_ParovaniVypisu` (CLUSTERED) — `ID`
