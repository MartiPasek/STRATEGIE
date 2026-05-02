# EC_Siemens_SeznamZakazek

**Schema**: dbo · **Cluster**: Other · **Rows**: 382 · **Size**: 0.33 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 3 | `CisloObjSiemens` | nvarchar(80) | ANO |  |  |
| 4 | `NazevProjektuSiemens` | nvarchar(80) | ANO |  |  |
| 5 | `CisloSkrine` | nvarchar(80) | ANO |  |  |
| 6 | `DatZadaniSiemens` | nvarchar(80) | ANO |  |  |
| 7 | `DatZahajeniSiemens` | nvarchar(80) | ANO |  |  |
| 8 | `DatUkonceniSiemens` | nvarchar(80) | ANO |  |  |
| 9 | `DatZahajeniEC` | datetime | ANO |  |  |
| 10 | `DatUkonceniEC` | datetime | ANO |  |  |
| 11 | `PlanZahajeniEC` | date | ANO |  |  |
| 12 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Siemens_SeznamZakazek` (CLUSTERED) — `ID`
