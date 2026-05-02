# EC_Vytizeni_DynamickeAkce

**Schema**: dbo · **Cluster**: Production · **Rows**: 4 · **Size**: 0.07 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nchar(255) | NE |  |  |
| 3 | `Poradi` | int | NE |  |  |
| 4 | `Typ` | int | NE |  |  |
| 5 | `Umisteni` | int | ANO |  | 0 = zakázky, 1 = plán |

## Indexy

- **PK** `PK_EC_Vytizeni_DynamickeAkce` (CLUSTERED) — `ID`
