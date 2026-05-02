# EC_KmenZbozi_Casti

**Schema**: dbo · **Cluster**: Production · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 8 · **FK**: 1 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | smallint | NE |  |  |
| 3 | `CastSkladu` | nvarchar(15) | NE |  |  |
| 4 | `Popis` | nvarchar(200) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `ID` → [`EC_KmenZbozi_Casti`](EC_KmenZbozi_Casti.md).`ID` _(constraint: `FK_EC_KmenZbozi_Casti_EC_KmenZbozi_Casti`)_

## Indexy

- **PK** `PK_EC_KmenZboziCasti` (CLUSTERED) — `ID`
- **UNIQUE** `IX_EC_KmenZbozi_Casti` (NONCLUSTERED) — `Cislo`
