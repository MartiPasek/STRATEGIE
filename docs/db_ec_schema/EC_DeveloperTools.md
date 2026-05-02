# EC_DeveloperTools

**Schema**: dbo · **Cluster**: Other · **Rows**: 21 · **Size**: 0.27 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(256) | NE | (suser_name()) |  |
| 3 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 4 | `Zmenil` | nvarchar(256) | ANO |  |  |
| 5 | `DatZmeny` | datetime | ANO |  |  |
| 6 | `TypID` | int | ANO |  |  |
| 7 | `Autor_CisloOrg` | int | ANO |  |  |
| 8 | `Autor_Text` | varchar(512) | ANO |  |  |
| 9 | `Prodavajici_CisloOrg` | int | ANO |  |  |
| 10 | `Prodavajici_Text` | varchar(512) | ANO |  |  |
| 11 | `Nazev` | varchar(256) | ANO |  |  |
| 12 | `Popis` | nvarchar(2000) | ANO |  |  |
| 13 | `Popis_instalace` | nvarchar(2000) | ANO |  |  |
| 23 | `Informace` | nvarchar(2000) | ANO |  |  |

## Indexy

- **PK** `PK_Table_1` (CLUSTERED) — `ID`
