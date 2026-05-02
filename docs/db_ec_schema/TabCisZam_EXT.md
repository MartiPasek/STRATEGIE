# TabCisZam_EXT

**Schema**: dbo · **Cluster**: Reference-Identity · **Rows**: 429 · **Size**: 0.34 MB · **Sloupců**: 61 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `_FPD` | float | ANO |  |  |
| 3 | `_FPDMax` | float | ANO |  |  |
| 4 | `_DPP_Kraceni` | smallint | ANO |  |  |
| 5 | `_ZaklMzda` | float | ANO |  |  |
| 6 | `_OsHodnoceni` | float | ANO |  |  |
| 7 | `_PremieVykon` | numeric(19,6) | ANO |  |  |
| 8 | `_neaktivni` | bit | ANO | ((0)) |  |
| 9 | `_DochazkaAutoOdhlasPo` | datetime | ANO |  |  |
| 10 | `_CasKontoMax` | int | ANO |  |  |
| 11 | `_Ukolnik` | bit | ANO | ((1)) |  |
| 12 | `_AuthDochazka` | nvarchar(1) | ANO | (N'U') |  |
| 13 | `_NeposilatSmerniceAUkoly` | bit | ANO |  |  |
| 14 | `_AuthFotoaparat` | nvarchar(1) | ANO | (N'U') |  |
| 15 | `_OSVC` | bit | ANO |  |  |
| 16 | `_DochazkaAutoPrihlas` | bit | ANO |  |  |
| 17 | `_DPP` | bit | ANO |  |  |
| 18 | `_HPP` | bit | ANO |  |  |
| 19 | `_DatumNastupu` | datetime | ANO |  |  |
| 20 | `_FPDGen` | int | ANO |  |  |
| 21 | `_VerzovaciZkratka` | nvarchar(3) | ANO |  |  |
| 22 | `_NarizenoVolno` | bit | ANO |  |  |
| 23 | `_NeplacenyPrescas` | numeric(19,6) | ANO |  |  |
| 24 | `_PoznamkaMzdy` | nvarchar(1000) | ANO |  |  |
| 25 | `_CisloOrgVazbaMzdy` | int | ANO |  |  |
| 26 | `_DatumOdchodu` | datetime | ANO |  |  |
| 27 | `_UzivJeSkupina` | bit | ANO |  |  |
| 28 | `_StravenkyOD` | datetime | ANO |  |  |
| 29 | `_TarifOD` | datetime | ANO |  |  |
| 30 | `_DovPrevedeno` | decimal(5,1) | ANO |  |  |
| 31 | `_DovPrevodZroku` | nvarchar(4) | ANO |  |  |
| 32 | `_BlokovatDochazku` | bit | ANO | ((0)) |  |
| 33 | `_Zkusebni` | bit | ANO |  |  |
| 34 | `_GenDochDoFPD` | bit | ANO | ((0)) |  |
| 35 | `_DatNeblokovatDochazku` | datetime | ANO |  |  |
| 36 | `_CentralaCryptUserName` | nvarchar(100) | ANO |  |  |
| 37 | `_CentralaCryptPassword` | nvarchar(100) | ANO |  |  |
| 38 | `_KontrolovatDochazku` | bit | ANO | ((1)) |  |
| 39 | `_CisloPohoda` | int | ANO |  |  |
| 40 | `_SchvalovatVolno` | bit | NE | ((1)) |  |
| 41 | `_NekontrolovatWorkReportDo` | date | ANO |  |  |
| 42 | `_Firma` | int | ANO | ((0)) |  |
| 43 | `_HesloVyplatnice` | int | ANO |  |  |
| 44 | `_SDPrevedeno` | numeric(19,6) | ANO |  |  |
| 45 | `_SDPrevodZRoku` | int | ANO |  |  |
| 46 | `_DovNPrevedeno` | numeric(19,6) | ANO |  |  |
| 47 | `_DovNPrevodZRoku` | int | ANO |  |  |
| 48 | `_NeupozornitNaNepritomnost` | bit | ANO | ((0)) |  |
| 49 | `_Naklady` | numeric(18,2) | ANO |  |  |
| 50 | `_Vynosy` | numeric(18,2) | ANO |  |  |
| 51 | `_Zisk` | numeric(18,2) | ANO |  |  |
| 52 | `_DatBlokaceDochazkyOD` | datetime | ANO |  |  |
| 53 | `_PrescasyNavrh` | bit | ANO |  |  |
| 54 | `_PrescasyNavrhl` | nvarchar(128) | ANO |  |  |
| 55 | `_VV_Poznamka` | nvarchar(500) | ANO |  |  |
| 56 | `_D_Kraceni` | numeric(9,2) | ANO | ((0)) |  |
| 57 | `_DN_Kraceni` | numeric(9,2) | ANO | ((0)) |  |
| 58 | `_SD_Kraceni` | numeric(9,2) | ANO | ((0)) |  |
| 59 | `_D_Kraceni_MinRok` | numeric(19,6) | ANO |  |  |
| 60 | `_DN_Kraceni_MinRok` | numeric(19,6) | ANO |  |  |
| 61 | `_SD_Kraceni_MinRok` | numeric(19,6) | ANO |  |  |

## Indexy

- **PK** `PK__TabCisZam_EXT__ID` (CLUSTERED) — `ID`
