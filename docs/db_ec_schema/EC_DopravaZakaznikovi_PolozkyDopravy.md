# EC_DopravaZakaznikovi_PolozkyDopravy

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,210 · **Size**: 1.12 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_DopravaZakaznikovi` | int | NE |  |  |
| 3 | `Popis` | nchar(100) | ANO |  |  |
| 4 | `Vyska` | int | ANO |  |  |
| 5 | `Sirka` | int | ANO |  |  |
| 6 | `Hloubka` | int | ANO |  |  |
| 7 | `Vaha` | int | ANO |  |  |
| 8 | `Kusu` | int | ANO |  |  |
| 9 | `Typ` | int | ANO | ((0)) | 0 = odhad VP, 1 = finální pro odvoz |
| 10 | `LzeNalozitZadyKsobe` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_DopravaZakaznikovi_PolozkyDopravy` (CLUSTERED) — `ID`
