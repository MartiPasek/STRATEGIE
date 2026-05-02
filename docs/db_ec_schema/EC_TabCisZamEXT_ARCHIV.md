# EC_TabCisZamEXT_ARCHIV

**Schema**: dbo · **Cluster**: Finance · **Rows**: 892 · **Size**: 0.47 MB · **Sloupců**: 54 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPuv` | int | ANO |  |  |
| 3 | `_FPD` | float | ANO |  |  |
| 4 | `_FPDMax` | float | ANO |  |  |
| 5 | `_DPP_Kraceni` | smallint | ANO |  |  |
| 6 | `_ZaklMzda` | float | ANO |  |  |
| 7 | `_OsHodnoceni` | float | ANO |  |  |
| 8 | `_PremieVykon` | numeric(19,6) | ANO |  |  |
| 9 | `_neaktivni` | bit | ANO | ((0)) |  |
| 10 | `_DochazkaAutoOdhlasPo` | datetime | ANO |  |  |
| 11 | `_CasKontoMax` | int | ANO |  |  |
| 12 | `_Ukolnik` | bit | ANO | ((1)) |  |
| 13 | `_AuthDochazka` | nvarchar(1) | ANO | (N'U') |  |
| 14 | `_NeposilatSmerniceAUkoly` | bit | ANO |  |  |
| 15 | `_AuthFotoaparat` | nvarchar(1) | ANO | (N'U') |  |
| 16 | `_OSVC` | bit | ANO |  |  |
| 17 | `_DochazkaAutoPrihlas` | bit | ANO |  |  |
| 18 | `_DPP` | bit | ANO |  |  |
| 19 | `_HPP` | bit | ANO |  |  |
| 20 | `_DatumNastupu` | datetime | ANO |  |  |
| 21 | `_FPDGen` | int | ANO |  |  |
| 22 | `_VerzovaciZkratka` | nvarchar(3) | ANO |  |  |
| 23 | `_NarizenoVolno` | bit | ANO |  |  |
| 24 | `_NeplacenyPrescas` | numeric(19,6) | ANO |  |  |
| 25 | `_PoznamkaMzdy` | nvarchar(1000) | ANO |  |  |
| 26 | `_CisloOrgVazbaMzdy` | int | ANO |  |  |
| 27 | `_DatumOdchodu` | datetime | ANO |  |  |
| 28 | `_UzivJeSkupina` | bit | ANO |  |  |
| 29 | `_StravenkyOD` | datetime | ANO |  |  |
| 30 | `_TarifOD` | datetime | ANO |  |  |
| 31 | `_DovPrevedeno` | decimal(5,1) | ANO |  |  |
| 32 | `_DovPrevodZroku` | nvarchar(4) | ANO |  |  |
| 33 | `_BlokovatDochazku` | bit | ANO | ((0)) |  |
| 34 | `_Zkusebni` | bit | ANO |  |  |
| 35 | `_GenDochDoFPD` | bit | ANO | ((0)) |  |
| 36 | `_DatNeblokovatDochazku` | datetime | ANO |  |  |
| 37 | `_CentralaCryptUserName` | nvarchar(100) | ANO |  |  |
| 38 | `_CentralaCryptPassword` | nvarchar(100) | ANO |  |  |
| 39 | `_KontrolovatDochazku` | bit | ANO | ((1)) |  |
| 40 | `_CisloPohoda` | int | ANO |  |  |
| 41 | `_SchvalovatVolno` | bit | NE | ((1)) |  |
| 42 | `_NekontrolovatWorkReportDo` | date | ANO |  |  |
| 43 | `_Firma` | int | ANO | ((0)) |  |
| 44 | `_HesloVyplatnice` | int | ANO |  |  |
| 45 | `_SDPrevedeno` | numeric(19,6) | ANO |  |  |
| 46 | `_SDPrevodZRoku` | int | ANO |  |  |
| 47 | `_DovNPrevedeno` | numeric(19,6) | ANO |  |  |
| 48 | `_DovNPrevodZRoku` | int | ANO |  |  |
| 49 | `_NeupozornitNaNepritomnost` | bit | ANO | ((0)) |  |
| 50 | `_Naklady` | numeric(18,2) | ANO |  |  |
| 51 | `_Vynosy` | numeric(18,2) | ANO |  |  |
| 52 | `_Zisk` | numeric(18,2) | ANO |  |  |
| 53 | `AutorArchivace` | nvarchar(128) | NE | (suser_sname()) |  |
| 54 | `DatArchivace` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_TabCisZamEXT_ARCHIV` (CLUSTERED) — `ID`
