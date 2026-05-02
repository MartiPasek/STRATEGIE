# EC_Dochazka_Tisk_gen

**Schema**: dbo · **Cluster**: HR · **Rows**: 644 · **Size**: 0.13 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 0

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
| 8 | `PrijmeniJmeno` | nvarchar(201) | ANO |  |  |
| 9 | `cislo` | int | ANO |  |  |
| 10 | `datum` | datetime | ANO |  |  |
| 11 | `je_st_svatek` | bit | NE |  |  |
| 12 | `Mesic` | int | ANO |  |  |
| 13 | `rok` | int | ANO |  |  |
| 14 | `Den` | varchar(7) | ANO |  |  |
| 15 | `Prichod` | varchar(4) | ANO |  |  |
| 16 | `Odchod` | varchar(5) | ANO |  |  |
| 17 | `Pauza` | varchar(4) | ANO |  |  |
| 18 | `Celkem` | varchar(4) | ANO |  |  |
| 19 | `Odpracovano` | varchar(4) | ANO |  |  |
| 20 | `sVATEK` | varchar(13) | NE |  |  |
| 21 | `Posledni` | int | NE |  |  |
