# EC_CenikyVazby

**Schema**: dbo · **Cluster**: Finance · **Rows**: 1,325 · **Size**: 0.14 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | smallint | ANO |  | 1 = Ceník na skupinu, 2 = Organizace na skupinu (IDZdrojTab = IDSkupiny, IDCilTab = ID Organizace), 3 = Ceník na zakázku |
| 3 | `ID_ZdrojTab` | int | ANO |  |  |
| 4 | `ID_CilTab` | int | ANO |  |  |
| 5 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
