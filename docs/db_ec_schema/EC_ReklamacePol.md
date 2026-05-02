# EC_ReklamacePol

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 197 · **Size**: 0.16 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | NE |  | ID z EC_Reklamace |
| 3 | `IDPolPohybZbo` | int | ANO |  | ID polozky z tabpohybyzbozi |
| 4 | `RegCis` | nvarchar(30) | NE |  |  |
| 5 | `CisloZakazky` | nvarchar(30) | ANO |  |  |
| 6 | `OdkudCislo` | int | ANO |  |  |
| 7 | `DodFak` | nvarchar(50) | ANO |  |  |
| 8 | `Mnozstvi` | numeric(19,6) | ANO |  |  |
| 9 | `PoznamkaTisk` | ntext | ANO |  |  |
| 10 | `PoznamkaInterni` | ntext | ANO |  |  |
| 11 | `Nazev1` | nvarchar(100) | ANO |  |  |
| 12 | `ResitelZakazky` | nvarchar(100) | ANO |  |  |
| 13 | `OrgZakazky` | nvarchar(150) | ANO |  |  |
| 14 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 15 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 16 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ReklamacePol` (CLUSTERED) — `ID`
