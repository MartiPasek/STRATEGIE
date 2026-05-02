# EC_IAP_TabZakazka_EXT

**Schema**: dbo · **Cluster**: Other · **Rows**: 4,035 · **Size**: 0.66 MB · **Sloupců**: 31 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `_Sefmonter` | nvarchar(20) | ANO |  |  |
| 3 | `_Uzavreno` | bit | ANO |  |  |
| 4 | `_KalkHodiny` | smallint | ANO |  |  |
| 5 | `_AbsolHodNakladVyroby` | smallint | ANO |  |  |
| 6 | `_HodinovyVynos` | int | ANO |  |  |
| 7 | `_HodinovyVynosKalk` | int | ANO |  |  |
| 8 | `_HrubyZiskDenik` | int | ANO |  |  |
| 9 | `_Kalk_VKM` | numeric(19,6) | ANO |  |  |
| 10 | `_KalkHodinyCelkem` | smallint | ANO |  |  |
| 11 | `_KalkHodinyNavic` | smallint | ANO |  |  |
| 12 | `_KalkKcCelkem` | int | ANO |  |  |
| 13 | `_KalkMarzeProc` | numeric(19,6) | ANO |  |  |
| 14 | `_KonecRealita` | datetime | ANO |  |  |
| 15 | `_NakladDenik` | int | ANO |  |  |
| 16 | `_NepocitatNV` | bit | ANO |  |  |
| 17 | `_PredpoklVynos` | int | ANO |  |  |
| 18 | `_RealHodiny` | int | ANO |  |  |
| 19 | `_RealKcCelkem` | int | ANO |  |  |
| 20 | `_RealVynos` | int | ANO |  |  |
| 21 | `_RezieSprava` | numeric(19,6) | ANO |  |  |
| 22 | `_RezieVKM` | numeric(19,6) | ANO |  |  |
| 23 | `_RezieVyroba` | numeric(19,6) | ANO |  |  |
| 24 | `_VynosDenik` | int | ANO |  |  |
| 25 | `_VyrobaHodNaklad` | smallint | ANO |  |  |
| 26 | `_VyrobaKalkHodNaklad` | smallint | ANO |  |  |
| 27 | `_FakturaceOKUziv` | bit | ANO |  |  |
| 28 | `_VypnoutKontroluKompletnosti` | int | ANO |  |  |
| 29 | `_FakturacePoznamka` | ntext | ANO |  |  |
| 30 | `_DatumKontrolyVykryti` | datetime | ANO |  |  |
| 31 | `_Zruseno` | bit | ANO |  |  |
