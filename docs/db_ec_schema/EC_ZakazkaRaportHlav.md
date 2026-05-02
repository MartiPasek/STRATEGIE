# EC_ZakazkaRaportHlav

**Schema**: dbo · **Cluster**: Finance · **Rows**: 0 · **Size**: 0.02 MB · **Sloupců**: 158 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `CisloZakazky` | varchar(15) | NE |  |  |
| 2 | `ZakazkaNazev` | varchar(30) | ANO |  |  |
| 3 | `ZakazkaDruhyNazev` | varchar(60) | ANO |  |  |
| 4 | `Datum` | datetime | ANO |  |  |
| 5 | `ObdobiOd` | datetime | ANO |  |  |
| 6 | `ObdobiDo` | datetime | ANO |  |  |
| 7 | `KalkHodiny` | int | ANO | ((0)) |  |
| 8 | `HodinyNavic` | int | ANO | ((0)) |  |
| 9 | `KalkHodinyCelkem` | int | ANO | ((0)) |  |
| 10 | `OdpracHodinyFyz` | int | NE | ((0)) |  |
| 11 | `OdpracHodinyPrep` | int | NE | ((0)) |  |
| 12 | `KalkulFinance` | int | ANO | ((0)) |  |
| 13 | `FinanceNavic` | int | ANO | ((0)) |  |
| 14 | `KalkFinanceCelkem` | int | ANO | ((0)) |  |
| 15 | `FinanceReal` | int | NE | ((0)) |  |
| 16 | `Zam01` | varchar(15) | ANO |  |  |
| 17 | `Zam02` | varchar(15) | ANO |  |  |
| 18 | `Zam03` | varchar(15) | ANO |  |  |
| 19 | `Zam04` | varchar(15) | ANO |  |  |
| 20 | `Zam05` | varchar(15) | ANO |  |  |
| 21 | `Zam06` | varchar(15) | ANO |  |  |
| 22 | `Zam07` | varchar(15) | ANO |  |  |
| 23 | `Zam08` | varchar(15) | ANO |  |  |
| 24 | `Zam09` | varchar(15) | ANO |  |  |
| 25 | `Zam10` | varchar(15) | ANO |  |  |
| 26 | `Zam11` | varchar(15) | ANO |  |  |
| 27 | `Zam12` | varchar(15) | ANO |  |  |
| 28 | `Zam13` | varchar(15) | ANO |  |  |
| 29 | `Zam14` | varchar(15) | ANO |  |  |
| 30 | `Zam15` | varchar(15) | ANO |  |  |
| 31 | `Zam16` | varchar(15) | ANO |  |  |
| 32 | `Zam17` | varchar(15) | ANO |  |  |
| 33 | `Zam18` | varchar(15) | ANO |  |  |
| 34 | `Zam19` | varchar(15) | ANO |  |  |
| 35 | `Zam20` | varchar(15) | ANO |  |  |
| 36 | `CisloZam01` | int | ANO |  |  |
| 37 | `CisloZam02` | int | ANO |  |  |
| 38 | `CisloZam03` | int | ANO |  |  |
| 39 | `CisloZam04` | int | ANO |  |  |
| 40 | `CisloZam05` | int | ANO |  |  |
| 41 | `CisloZam06` | int | ANO |  |  |
| 42 | `CisloZam07` | int | ANO |  |  |
| 43 | `CisloZam08` | int | ANO |  |  |
| 44 | `CisloZam09` | int | ANO |  |  |
| 45 | `CisloZam10` | int | ANO |  |  |
| 46 | `CisloZam11` | int | ANO |  |  |
| 47 | `CisloZam12` | int | ANO |  |  |
| 48 | `CisloZam13` | int | ANO |  |  |
| 49 | `CisloZam14` | int | ANO |  |  |
| 50 | `CisloZam15` | int | ANO |  |  |
| 51 | `CisloZam16` | int | ANO |  |  |
| 52 | `CisloZam17` | int | ANO |  |  |
| 53 | `CisloZam18` | int | ANO |  |  |
| 54 | `CisloZam19` | int | ANO |  |  |
| 55 | `CisloZam20` | int | ANO |  |  |
| 56 | `CelPredpFinZam01` | int | ANO |  |  |
| 57 | `CelPredpFinZam02` | int | ANO |  |  |
| 58 | `CelPredpFinZam03` | int | ANO |  |  |
| 59 | `CelPredpFinZam04` | int | ANO |  |  |
| 60 | `CelPredpFinZam05` | int | ANO |  |  |
| 61 | `CelPredpFinZam06` | int | ANO |  |  |
| 62 | `CelPredpFinZam07` | int | ANO |  |  |
| 63 | `CelPredpFinZam08` | int | ANO |  |  |
| 64 | `CelPredpFinZam09` | int | ANO |  |  |
| 65 | `CelPredpFinZam10` | int | ANO |  |  |
| 66 | `CelPredpFinZam11` | int | ANO |  |  |
| 67 | `CelPredpFinZam12` | int | ANO |  |  |
| 68 | `CelPredpFinZam13` | int | ANO |  |  |
| 69 | `CelPredpFinZam14` | int | ANO |  |  |
| 70 | `CelPredpFinZam15` | int | ANO |  |  |
| 71 | `CelPredpFinZam16` | int | ANO |  |  |
| 72 | `CelPredpFinZam17` | int | ANO |  |  |
| 73 | `CelPredpFinZam18` | int | ANO |  |  |
| 74 | `CelPredpFinZam19` | int | ANO |  |  |
| 75 | `CelPredpFinZam20` | int | ANO |  |  |
| 76 | `CelPredpFin` | int | ANO |  |  |
| 77 | `HodPredpFinZam01` | int | ANO |  |  |
| 78 | `HodPredpFinZam02` | int | ANO |  |  |
| 79 | `HodPredpFinZam03` | int | ANO |  |  |
| 80 | `HodPredpFinZam04` | int | ANO |  |  |
| 81 | `HodPredpFinZam05` | int | ANO |  |  |
| 82 | `HodPredpFinZam06` | int | ANO |  |  |
| 83 | `HodPredpFinZam07` | int | ANO |  |  |
| 84 | `HodPredpFinZam08` | int | ANO |  |  |
| 85 | `HodPredpFinZam09` | int | ANO |  |  |
| 86 | `HodPredpFinZam10` | int | ANO |  |  |
| 87 | `HodPredpFinZam11` | int | ANO |  |  |
| 88 | `HodPredpFinZam12` | int | ANO |  |  |
| 89 | `HodPredpFinZam13` | int | ANO |  |  |
| 90 | `HodPredpFinZam14` | int | ANO |  |  |
| 91 | `HodPredpFinZam15` | int | ANO |  |  |
| 92 | `HodPredpFinZam16` | int | ANO |  |  |
| 93 | `HodPredpFinZam17` | int | ANO |  |  |
| 94 | `HodPredpFinZam18` | int | ANO |  |  |
| 95 | `HodPredpFinZam19` | int | ANO |  |  |
| 96 | `HodPredpFinZam20` | int | ANO |  |  |
| 97 | `CelRealFin` | int | ANO | ((0)) |  |
| 98 | `CelRealFinZam01` | int | ANO |  |  |
| 99 | `CelRealFinZam02` | int | ANO |  |  |
| 100 | `CelRealFinZam03` | int | ANO |  |  |
| 101 | `CelRealFinZam04` | int | ANO |  |  |
| 102 | `CelRealFinZam05` | int | ANO |  |  |
| 103 | `CelRealFinZam06` | int | ANO |  |  |
| 104 | `CelRealFinZam07` | int | ANO |  |  |
| 105 | `CelRealFinZam08` | int | ANO |  |  |
| 106 | `CelRealFinZam09` | int | ANO |  |  |
| 107 | `CelRealFinZam10` | int | ANO |  |  |
| 108 | `CelRealFinZam11` | int | ANO |  |  |
| 109 | `CelRealFinZam12` | int | ANO |  |  |
| 110 | `CelRealFinZam13` | int | ANO |  |  |
| 111 | `CelRealFinZam14` | int | ANO |  |  |
| 112 | `CelRealFinZam15` | int | ANO |  |  |
| 113 | `CelRealFinZam16` | int | ANO |  |  |
| 114 | `CelRealFinZam17` | int | ANO |  |  |
| 115 | `CelRealFinZam18` | int | ANO |  |  |
| 116 | `CelRealFinZam19` | int | ANO |  |  |
| 117 | `CelRealFinZam20` | int | ANO |  |  |
| 118 | `HodRealFinZam01` | int | ANO |  |  |
| 119 | `HodRealFinZam02` | int | ANO |  |  |
| 120 | `HodRealFinZam03` | int | ANO |  |  |
| 121 | `HodRealFinZam04` | int | ANO |  |  |
| 122 | `HodRealFinZam05` | int | ANO |  |  |
| 123 | `HodRealFinZam06` | int | ANO |  |  |
| 124 | `HodRealFinZam07` | int | ANO |  |  |
| 125 | `HodRealFinZam08` | int | ANO |  |  |
| 126 | `HodRealFinZam09` | int | ANO |  |  |
| 127 | `HodRealFinZam10` | int | ANO |  |  |
| 128 | `HodRealFinZam11` | int | ANO |  |  |
| 129 | `HodRealFinZam12` | int | ANO |  |  |
| 130 | `HodRealFinZam13` | int | ANO |  |  |
| 131 | `HodRealFinZam14` | int | ANO |  |  |
| 132 | `HodRealFinZam15` | int | ANO |  |  |
| 133 | `HodRealFinZam16` | int | ANO |  |  |
| 134 | `HodRealFinZam17` | int | ANO |  |  |
| 135 | `HodRealFinZam18` | int | ANO |  |  |
| 136 | `HodRealFinZam19` | int | ANO |  |  |
| 137 | `HodRealFinZam20` | int | ANO |  |  |
| 138 | `PremieCelkem` | int | ANO |  |  |
| 139 | `PremieZam01` | int | ANO |  |  |
| 140 | `PremieZam02` | int | ANO |  |  |
| 141 | `PremieZam03` | int | ANO |  |  |
| 142 | `PremieZam04` | int | ANO |  |  |
| 143 | `PremieZam05` | int | ANO |  |  |
| 144 | `PremieZam06` | int | ANO |  |  |
| 145 | `PremieZam07` | int | ANO |  |  |
| 146 | `PremieZam08` | int | ANO |  |  |
| 147 | `PremieZam09` | int | ANO |  |  |
| 148 | `PremieZam10` | int | ANO |  |  |
| 149 | `PremieZam11` | int | ANO |  |  |
| 150 | `PremieZam12` | int | ANO |  |  |
| 151 | `PremieZam13` | int | ANO |  |  |
| 152 | `PremieZam14` | int | ANO |  |  |
| 153 | `PremieZam15` | int | ANO |  |  |
| 154 | `PremieZam16` | int | ANO |  |  |
| 155 | `PremieZam17` | int | ANO |  |  |
| 156 | `PremieZam18` | int | ANO |  |  |
| 157 | `PremieZam19` | int | ANO |  |  |
| 158 | `PremieZam20` | int | ANO |  |  |
