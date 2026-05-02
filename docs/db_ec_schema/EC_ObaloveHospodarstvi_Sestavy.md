# EC_ObaloveHospodarstvi_Sestavy

**Schema**: dbo · **Cluster**: Other · **Rows**: 3,113 · **Size**: 2.29 MB · **Sloupců**: 40 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Zakazka` | nvarchar(20) | ANO |  |  |
| 3 | `Sestava` | nvarchar(100) | ANO |  |  |
| 4 | `Vyska_mm` | numeric(18,6) | ANO |  |  |
| 5 | `Sirka_mm` | numeric(18,6) | ANO |  |  |
| 6 | `Delka_mm` | numeric(18,6) | ANO |  |  |
| 7 | `Obvod_mm` | numeric(18,6) | ANO |  |  |
| 8 | `Povrch_m2` | numeric(18,6) | ANO |  |  |
| 9 | `Objem_m2` | numeric(18,6) | ANO |  |  |
| 10 | `StrecFolie_m` | numeric(18,6) | ANO |  |  |
| 11 | `StrecFolie_kg` | numeric(18,6) | ANO |  |  |
| 12 | `MnozstviRoleStrecFolie_perc` | numeric(18,6) | ANO |  |  |
| 13 | `KartonRittal_kg` | numeric(18,6) | ANO |  |  |
| 14 | `VlnLepenkaJunker_m` | numeric(18,6) | ANO |  |  |
| 15 | `VlnLepenkaJunker_kg` | numeric(18,6) | ANO |  |  |
| 16 | `MnozstviRoleVlnLepenkaJunker_perc` | numeric(18,6) | ANO |  |  |
| 17 | `VlnLepenkaEC_m` | numeric(18,6) | ANO |  |  |
| 18 | `VlnLepenkaEC_kg` | numeric(18,6) | ANO |  |  |
| 19 | `MnozstviRoleVlnLepenkaEC_perc` | numeric(18,6) | ANO |  |  |
| 20 | `RohoveVystuze4ks_kg` | numeric(18,6) | ANO |  |  |
| 21 | `PocetKrabic_c1` | numeric(18,6) | ANO |  |  |
| 22 | `PocetKrabic_c2` | numeric(18,6) | ANO |  |  |
| 23 | `PocetKrabic_c3` | numeric(18,6) | ANO |  |  |
| 24 | `PocetKrabic_c4` | numeric(18,6) | ANO |  |  |
| 25 | `KrabicePribal_kg` | numeric(18,6) | ANO |  |  |
| 26 | `PocetEuPalet` | numeric(18,6) | ANO |  |  |
| 27 | `PocetRittalPalet` | numeric(18,6) | ANO |  |  |
| 28 | `PocetMensichPalet` | numeric(18,6) | ANO |  |  |
| 29 | `Palety_kg` | numeric(18,6) | ANO |  |  |
| 30 | `Miralon_m` | numeric(18,6) | ANO |  |  |
| 31 | `Miralon_kg` | numeric(18,6) | ANO |  |  |
| 32 | `BubliFolie_m` | numeric(18,6) | ANO |  |  |
| 33 | `BubliFolie_kg` | numeric(18,6) | ANO |  |  |
| 34 | `VazaciPaska_m` | numeric(18,6) | ANO |  |  |
| 35 | `VazaciPaska_kg` | numeric(18,6) | ANO |  |  |
| 36 | `Autor` | nvarchar(128) | ANO |  |  |
| 37 | `DatPorizeni` | datetime | ANO |  |  |
| 38 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 39 | `DatZmeny` | datetime | ANO |  |  |
| 40 | `Skrin_PocetKusu` | numeric(18,6) | ANO |  |  |

## Indexy

- **PK** `PK_EC_ObaloveHospodarstvi_Sestavy` (CLUSTERED) — `ID`
