# EC_Dochazka_Tisk_9MESIC

**Schema**: dbo · **Cluster**: HR · **Rows**: 695 · **Size**: 0.14 MB · **Sloupců**: 22 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Dovolena` | numeric(17,6) | NE |  |  |
| 2 | `Lekar` | numeric(17,6) | NE |  |  |
| 3 | `Nemoc` | numeric(17,6) | NE |  |  |
| 4 | `OCR` | numeric(17,6) | NE |  |  |
| 5 | `PracUraz` | numeric(17,6) | NE |  |  |
| 6 | `Paragraf` | numeric(17,6) | NE |  |  |
| 7 | `Ostatni` | numeric(17,6) | NE |  |  |
| 8 | `id` | int | ANO |  |  |
| 9 | `PrijmeniJmeno` | nvarchar(201) | ANO |  |  |
| 10 | `cislo` | int | ANO |  |  |
| 11 | `datum` | datetime | ANO |  |  |
| 12 | `je_st_svatek` | int | NE |  |  |
| 13 | `Mesic` | int | ANO |  |  |
| 14 | `rok` | int | ANO |  |  |
| 15 | `Den` | varchar(7) | ANO |  |  |
| 16 | `Prichod` | varchar(4) | ANO |  |  |
| 17 | `Odchod` | varchar(5) | ANO |  |  |
| 18 | `Pauza` | varchar(4) | ANO |  |  |
| 19 | `Celkem` | varchar(4) | ANO |  |  |
| 20 | `Odpracovano` | varchar(4) | ANO |  |  |
| 21 | `sVATEK` | varchar(13) | NE |  |  |
| 22 | `Posledni` | int | NE |  |  |
