# EC_KalkCenaKontrolaTemp

**Schema**: dbo · **Cluster**: Production · **Rows**: 10,410 · **Size**: 0.95 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | NE |  |  |
| 3 | `CenikNC` | numeric(18,2) | ANO |  |  |
| 4 | `CenikPC` | numeric(18,2) | ANO |  |  |
| 5 | `CenikMena` | nvarchar(3) | ANO | (N'EUR') |  |
| 6 | `CenikPlatnost` | datetime | ANO |  |  |
| 7 | `CenikOrg` | int | ANO |  |  |
| 8 | `CenikOrgNazev` | nvarchar(100) | ANO |  |  |
| 9 | `PoslNakupCena` | numeric(18,2) | ANO |  |  |
| 10 | `PoslNakupMena` | nvarchar(3) | ANO |  |  |
| 11 | `PoslNakupDatum` | datetime | ANO |  |  |
| 12 | `PoslNakupOrg` | int | ANO |  |  |
| 13 | `PoslNakupOrgNazev` | nvarchar(100) | ANO |  |  |
| 14 | `VyjimkaMJ` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkCenaKontrolaTemp` (CLUSTERED) — `ID`
