# EC_OrgPost

**Schema**: dbo · **Cluster**: HR · **Rows**: 126 · **Size**: 0.13 MB · **Sloupců**: 17 · **FK**: 1 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | NE |  |  |
| 3 | `Nazev` | nvarchar(255) | ANO |  |  |
| 4 | `ID_NadrazenyPost` | int | ANO |  |  |
| 5 | `NazevNadrazenehoPostu` | nvarchar(255) | ANO |  |  |
| 6 | `Produkt` | nvarchar(MAX) | ANO | ('') |  |
| 7 | `Poznamka` | nvarchar(255) | ANO | ('') |  |
| 8 | `Aktivni` | bit | ANO | ((0)) |  |
| 9 | `Divize` | tinyint | ANO |  |  |
| 10 | `Odsazeni` | tinyint | ANO |  |  |
| 11 | `Poradi` | nvarchar(7) | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
| 16 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 17 | `DatZamceni` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `Cislo` → [`EC_OrgPost`](EC_OrgPost.md).`Cislo` _(constraint: `FK_EC_OrgPost_EC_OrgPost`)_

## Indexy

- **PK** `PK_EC_OrgPost` (CLUSTERED) — `ID`
- **UNIQUE** `IX_EC_OrgPost` (NONCLUSTERED) — `Cislo`
