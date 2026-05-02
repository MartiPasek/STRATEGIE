# EC_Obedy_Objednani

**Schema**: dbo · **Cluster**: Other · **Rows**: 339,900 · **Size**: 48.38 MB · **Sloupců**: 30 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Datum` | datetime | ANO |  |  |
| 4 | `Pol1` | int | ANO |  |  |
| 5 | `Pol2` | int | ANO |  |  |
| 6 | `Jidlo1` | int | ANO |  |  |
| 7 | `Jidlo2` | int | ANO |  |  |
| 8 | `Jidlo3` | int | ANO |  |  |
| 9 | `Jidlo4` | int | ANO |  |  |
| 10 | `Jidlo5` | int | ANO |  |  |
| 11 | `Jidlo6` | int | ANO |  |  |
| 12 | `Jidlo7` | int | ANO |  |  |
| 13 | `Jidlo8` | int | ANO |  |  |
| 14 | `Jidlo9` | int | ANO |  |  |
| 15 | `Jidlo10` | int | ANO |  |  |
| 16 | `Jidlo11` | int | ANO |  |  |
| 17 | `Jidlo12` | int | ANO |  |  |
| 18 | `Jidlo13` | int | ANO |  |  |
| 19 | `Jidlo14` | int | ANO |  |  |
| 20 | `Jidlo15` | int | ANO |  |  |
| 21 | `Jidlo16` | int | ANO |  |  |
| 22 | `Jidlo17` | int | ANO |  |  |
| 23 | `Jidlo18` | int | ANO |  |  |
| 24 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 25 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 26 | `Vzor` | bit | ANO |  |  |
| 27 | `Zpracovano` | bit | ANO |  |  |
| 28 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 29 | `DatZmeny` | datetime | ANO |  |  |
| 30 | `Cena` | int | ANO |  |  |
