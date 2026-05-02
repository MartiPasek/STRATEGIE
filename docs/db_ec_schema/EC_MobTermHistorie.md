# EC_MobTermHistorie

**Schema**: dbo · **Cluster**: Other · **Rows**: 346,356 · **Size**: 64.45 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `idZdrojZaznamu` | int | ANO |  |  |
| 2 | `ZdrojTabulka` | nvarchar(50) | ANO |  |  |
| 3 | `DruhProcesu` | int | ANO |  |  |
| 4 | `PoradoveCislo` | int | ANO |  |  |
| 5 | `RegCis` | nvarchar(30) | ANO |  |  |
| 6 | `Barcode` | nvarchar(100) | ANO |  |  |
| 7 | `Mnozstvi` | numeric(19,6) | ANO |  |  |
| 8 | `DatumVlozeni` | datetime | ANO |  |  |
| 9 | `Autor` | int | ANO |  |  |
| 10 | `DruhVlozeni` | nvarchar(50) | ANO |  |  |
