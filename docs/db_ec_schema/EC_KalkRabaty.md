# EC_KalkRabaty

**Schema**: dbo · **Cluster**: Production · **Rows**: 2,466 · **Size**: 0.57 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | NE |  |  |
| 3 | `Typ` | tinyint | NE |  |  |
| 4 | `TypText` | varchar(8) | NE |  |  |
| 5 | `Rabat` | numeric(6,1) | ANO |  |  |
| 6 | `CisloOrg` | int | ANO |  |  |
| 7 | `CisloOrgDod` | int | ANO |  |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `Blokovano` | bit | ANO | ((0)) |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `IndArchiv` | int | NE |  |  |
| 15 | `CenaCZK` | numeric(18,2) | ANO |  |  |
| 16 | `MenaCZK` | int | NE |  |  |
| 17 | `CenaCzkL` | numeric(31,10) | ANO |  |  |
| 18 | `CenaL` | numeric(38,11) | ANO |  |  |
| 19 | `CenaN` | numeric(38,16) | ANO |  |  |
| 20 | `EURKurz` | numeric(19,6) | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkRabaty` (CLUSTERED) — `ID`
