# EC_Svatky

**Schema**: dbo · **Cluster**: Other · **Rows**: 6,209 · **Size**: 0.60 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 4

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `den` | char(2) | ANO |  |  |
| 3 | `mesic` | char(2) | ANO |  |  |
| 4 | `rok` | char(4) | ANO |  |  |
| 5 | `jmeno` | varchar(50) | ANO | (NULL) |  |
| 6 | `svatek` | varchar(50) | ANO | (NULL) |  |
| 7 | `je_st_svatek` | int | NE |  |  |
| 8 | `je_prac_volno` | bit | NE | ((0)) |  |
| 9 | `je_prac_den` | bit | NE | ((0)) |  |
| 10 | `den_integer` | int | ANO |  |  |
| 11 | `mesic_integer` | int | ANO |  |  |
| 12 | `rok_integer` | int | ANO |  |  |
| 13 | `datum` | varchar(10) | ANO |  |  |
| 14 | `tyden` | char(2) | ANO |  |  |
| 15 | `tyden_integer` | int | ANO |  |  |
| 16 | `den_text` | nvarchar(10) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Svatky` (CLUSTERED) — `ID`
- **INDEX** `svatek_datum_key` (NONCLUSTERED) — `den, mesic`
- **INDEX** `svatek_jmeno_key` (NONCLUSTERED) — `jmeno`
- **INDEX** `IX_EC_SVATKY_BY_PRACDEN_ROK` (NONCLUSTERED) — `datum, je_prac_den, rok_integer`
