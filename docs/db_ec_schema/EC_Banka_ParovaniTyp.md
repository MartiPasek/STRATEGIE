# EC_Banka_ParovaniTyp

**Schema**: dbo · **Cluster**: Finance · **Rows**: 11 · **Size**: 0.07 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | nvarchar(30) | NE |  |  |
| 3 | `Popis` | nvarchar(50) | ANO |  |  |
| 4 | `UcetniUcet` | nvarchar(40) | ANO |  |  |
| 5 | `Stredisko` | nvarchar(30) | ANO |  |  |
| 6 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 7 | `CisloOrg` | int | ANO |  |  |
| 8 | `Upozorneni` | nvarchar(50) | ANO |  |  |
| 9 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Banka_ParovaniTyp` (CLUSTERED) — `ID`
