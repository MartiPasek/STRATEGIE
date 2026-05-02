# EC_Pripominky

**Schema**: dbo · **Cluster**: CRM · **Rows**: 20 · **Size**: 0.07 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `TypPripominky` | int | ANO |  |  |
| 3 | `TerminPripominky` | datetime | ANO |  |  |
| 4 | `Zadavatel` | int | ANO |  |  |
| 5 | `Resitel` | nvarchar(255) | ANO |  |  |
| 6 | `Kopie` | nvarchar(255) | ANO |  |  |
| 7 | `Predmet` | nvarchar(255) | ANO |  |  |
| 8 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 9 | `CisloZakazky` | nvarchar(50) | ANO |  |  |
| 10 | `IDPolozky` | int | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Pripominky` (CLUSTERED) — `ID`
