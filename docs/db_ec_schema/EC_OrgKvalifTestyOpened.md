# EC_OrgKvalifTestyOpened

**Schema**: dbo · **Cluster**: HR · **Rows**: 12,207 · **Size**: 1.01 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Otazka` | int | ANO |  |  |
| 4 | `Sestava` | int | ANO |  |  |
| 5 | `Odpoved` | int | ANO |  |  |
| 6 | `Kontrola` | bit | ANO |  |  |
| 7 | `Vyhodnoceno` | bit | NE | ((0)) |  |
| 8 | `Neverejna` | bit | ANO |  |  |
| 9 | `Odmitnuta` | bit | ANO |  |  |
| 10 | `Poradi` | int | ANO |  |  |
| 11 | `CasZobrazeni` | datetime | ANO |  |  |
| 12 | `DobaReseni` | int | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_OrgKvalifTestyOpened` (CLUSTERED) — `ID`
- **INDEX** `IX_EC_OrgKvalifTestyOpened_CisloZam,SestavaCasZobrazeni` (NONCLUSTERED) — `CisloZam, Sestava, CasZobrazeni`
