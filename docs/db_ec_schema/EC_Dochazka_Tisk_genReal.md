# EC_Dochazka_Tisk_genReal

**Schema**: dbo · **Cluster**: HR · **Rows**: 28,783 · **Size**: 6.14 MB · **Sloupců**: 26 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Dovolena` | numeric(17,6) | NE |  |  |
| 3 | `Lekar` | numeric(17,6) | NE |  |  |
| 4 | `Nemoc` | numeric(17,6) | NE |  |  |
| 5 | `OCR` | numeric(17,6) | NE |  |  |
| 6 | `PracUraz` | numeric(17,6) | NE |  |  |
| 7 | `Paragraf` | numeric(17,6) | NE |  |  |
| 8 | `Ostatni` | numeric(17,6) | NE |  |  |
| 9 | `PrichodReal` | datetime | ANO |  |  |
| 10 | `PauzaOdchod` | datetime | ANO |  |  |
| 11 | `OdchodReal` | datetime | ANO |  |  |
| 12 | `PrijmeniJmeno` | nvarchar(201) | ANO |  |  |
| 13 | `cislo` | int | ANO |  |  |
| 14 | `datum` | datetime | ANO |  |  |
| 15 | `je_st_svatek` | bit | NE |  |  |
| 16 | `Mesic` | int | ANO |  |  |
| 17 | `rok` | int | ANO |  |  |
| 18 | `Den` | varchar(7) | ANO |  |  |
| 19 | `Prichod` | datetime | ANO |  |  |
| 20 | `Odchod` | datetime | ANO |  |  |
| 21 | `Pauza` | varchar(4) | ANO |  |  |
| 22 | `Celkem` | varchar(4) | ANO |  |  |
| 23 | `Odpracovano` | varchar(4) | ANO |  |  |
| 24 | `sVATEK` | varchar(13) | NE |  |  |
| 25 | `Posledni` | int | NE |  |  |
| 26 | `pauzaPrichod` | datetime | ANO |  |  |
