# EC_ZamDovolene

**Schema**: dbo · **Cluster**: Other · **Rows**: 586 · **Size**: 0.36 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Cislo` | int | NE |  |  |
| 2 | `LoginID` | nvarchar(128) | NE |  |  |
| 3 | `Jmeno` | nvarchar(100) | NE |  |  |
| 4 | `Prijmeni` | nvarchar(100) | NE |  |  |
| 5 | `DruhSmlouvyText` | varchar(12) | ANO |  |  |
| 6 | `_Neaktivni` | bit | ANO |  |  |
| 7 | `NarokD` | nvarchar(20) | ANO |  |  |
| 8 | `ZbyvaD` | nvarchar(20) | ANO |  |  |
| 9 | `NarokDN` | nvarchar(20) | ANO |  |  |
| 10 | `ZbyvaDN` | nvarchar(20) | ANO |  |  |
| 11 | `NarokSD` | nvarchar(20) | ANO |  |  |
| 12 | `ZbyvaSD` | nvarchar(20) | ANO |  |  |
| 13 | `naplanovano` | nvarchar(20) | ANO |  |  |
| 14 | `naplanovanoSD` | nvarchar(20) | ANO |  |  |
| 15 | `ROK_VYPOCTU` | int | ANO |  |  |
| 16 | `PrevedenaD` | nvarchar(20) | ANO | ('0.0') |  |
| 17 | `PrevedenaD_Rok` | int | ANO |  |  |
