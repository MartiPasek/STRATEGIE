# TabCisOrg

**Schema**: dbo · **Cluster**: Reference-Identity · **Rows**: 1,972 · **Size**: 3.64 MB · **Sloupců**: 280 · **FK**: 29 · **Indexů**: 4

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloOrg` | int | NE |  |  |
| 3 | `NadrizenaOrg` | int | ANO |  |  |
| 4 | `Nazev` | nvarchar(255) | NE | ('') |  |
| 5 | `DruhyNazev` | nvarchar(100) | NE | ('') |  |
| 6 | `Misto` | nvarchar(100) | NE | ('') |  |
| 7 | `IdZeme` | nvarchar(3) | ANO |  |  |
| 8 | `Region` | nvarchar(15) | ANO |  |  |
| 9 | `Ulice` | nvarchar(100) | NE | ('') |  |
| 10 | `OrCislo` | nvarchar(15) | NE | ('') |  |
| 11 | `PopCislo` | nvarchar(15) | NE | ('') |  |
| 12 | `PSC` | nvarchar(10) | ANO |  |  |
| 13 | `PoBox` | nvarchar(40) | ANO |  |  |
| 14 | `Kontakt` | nvarchar(40) | ANO |  |  |
| 15 | `DIC` | nvarchar(15) | ANO |  |  |
| 16 | `LhutaSplatnosti` | smallint | ANO |  |  |
| 17 | `Stav` | tinyint | NE | ((0)) |  |
| 18 | `PravniForma` | tinyint | NE | ((0)) |  |
| 19 | `DruhCinnosti` | int | ANO |  |  |
| 20 | `ICO` | nvarchar(20) | ANO |  |  |
| 21 | `Sleva` | numeric(5,2) | NE | ((0.0)) |  |
| 22 | `OdHodnoty` | numeric(19,6) | NE | ((0.0)) |  |
| 23 | `CenovaUroven` | int | ANO |  |  |
| 24 | `IDSOZsleva` | int | ANO |  |  |
| 25 | `IDSOZnazev` | int | ANO |  |  |
| 26 | `Poznamka` | ntext | ANO |  |  |
| 27 | `FormaUhrady` | nvarchar(30) | ANO |  |  |
| 28 | `JeOdberatel` | bit | NE | ((0)) |  |
| 29 | `JeDodavatel` | bit | NE | ((0)) |  |
| 30 | `VernostniProgram` | bit | NE | ((0)) |  |
| 31 | `OdpOs` | int | ANO |  |  |
| 32 | `Upozorneni` | nvarchar(255) | ANO |  |  |
| 33 | `CisloOrgDos` | nvarchar(20) | NE | ('') |  |
| 34 | `Mena` | nvarchar(3) | ANO |  |  |
| 35 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 36 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 37 | `DatZmeny` | datetime | ANO |  |  |
| 38 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 39 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 40 | `Fakturacni` | bit | NE | ((0)) |  |
| 41 | `MU` | bit | NE | ((0)) |  |
| 42 | `Prijemce` | bit | NE | ((0)) |  |
| 43 | `UdajOZapisuDoObchRej` | nvarchar(128) | NE | ('') |  |
| 44 | `IDBankSpojeni` | int | ANO |  |  |
| 45 | `CarovyKodEAN` | nvarchar(13) | ANO |  |  |
| 46 | `PostAddress` | nvarchar(255) | NE | ('') |  |
| 47 | `Kredit` | numeric(19,6) | NE | ((0.0)) |  |
| 48 | `Saldo` | numeric(19,6) | NE | ((0.0)) |  |
| 49 | `UhrazenoPredSpl1` | numeric(19,6) | NE | ((0.0)) |  |
| 50 | `UhrazenoPredSpl2` | numeric(19,6) | NE | ((0.0)) |  |
| 51 | `UhrazenoPredSpl3` | numeric(19,6) | NE | ((0.0)) |  |
| 52 | `UhrazenoPredSpl4` | numeric(19,6) | NE | ((0.0)) |  |
| 53 | `UhrazenoPredSpl5` | numeric(19,6) | NE | ((0.0)) |  |
| 54 | `UhrazenoPredSpl6` | numeric(19,6) | NE | ((0.0)) |  |
| 55 | `UhrazenoPredSpl0` | numeric(19,6) | NE | ((0.0)) |  |
| 56 | `UhrazenoPoSpl1` | numeric(19,6) | NE | ((0.0)) |  |
| 57 | `UhrazenoPoSpl2` | numeric(19,6) | NE | ((0.0)) |  |
| 58 | `UhrazenoPoSpl3` | numeric(19,6) | NE | ((0.0)) |  |
| 59 | `UhrazenoPoSpl4` | numeric(19,6) | NE | ((0.0)) |  |
| 60 | `UhrazenoPoSpl5` | numeric(19,6) | NE | ((0.0)) |  |
| 61 | `UhrazenoPoSpl6` | numeric(19,6) | NE | ((0.0)) |  |
| 62 | `UhrazenoPoSpl0` | numeric(19,6) | NE | ((0.0)) |  |
| 63 | `NeuhrazenoPredSpl1` | numeric(19,6) | NE | ((0.0)) |  |
| 64 | `NeuhrazenoPredSpl2` | numeric(19,6) | NE | ((0.0)) |  |
| 65 | `NeuhrazenoPredSpl3` | numeric(19,6) | NE | ((0.0)) |  |
| 66 | `NeuhrazenoPredSpl4` | numeric(19,6) | NE | ((0.0)) |  |
| 67 | `NeuhrazenoPredSpl5` | numeric(19,6) | NE | ((0.0)) |  |
| 68 | `NeuhrazenoPredSpl6` | numeric(19,6) | NE | ((0.0)) |  |
| 69 | `NeuhrazenoPredSpl0` | numeric(19,6) | NE | ((0.0)) |  |
| 70 | `NeuhrazenoPoSpl1` | numeric(19,6) | NE | ((0.0)) |  |
| 71 | `NeuhrazenoPoSpl2` | numeric(19,6) | NE | ((0.0)) |  |
| 72 | `NeuhrazenoPoSpl3` | numeric(19,6) | NE | ((0.0)) |  |
| 73 | `NeuhrazenoPoSpl4` | numeric(19,6) | NE | ((0.0)) |  |
| 74 | `NeuhrazenoPoSpl5` | numeric(19,6) | NE | ((0.0)) |  |
| 75 | `NeuhrazenoPoSpl6` | numeric(19,6) | NE | ((0.0)) |  |
| 76 | `NeuhrazenoPoSpl0` | numeric(19,6) | NE | ((0.0)) |  |
| 77 | `FaSumaCelkem` | numeric(19,6) | ANO | ((0.0)) |  |
| 78 | `PozastavenoCelkem` | numeric(19,6) | ANO | ((0.0)) |  |
| 79 | `FaAktualizovano` | datetime | ANO |  |  |
| 80 | `PlneniBezDPH` | bit | NE | ((0)) |  |
| 81 | `Jazyk` | nvarchar(15) | ANO |  |  |
| 82 | `DatumNeupominani` | datetime | ANO |  |  |
| 83 | `CenovaUrovenNakup` | int | ANO |  |  |
| 84 | `TIN` | nvarchar(17) | NE | ('') |  |
| 85 | `EvCisDanovySklad` | nvarchar(30) | ANO |  |  |
| 86 | `DICsk` | nvarchar(15) | ANO |  |  |
| 87 | `SlevaSozNa` | tinyint | ANO | ((2)) |  |
| 88 | `SlevaSkupZbo` | tinyint | ANO | ((2)) |  |
| 89 | `SlevaKmenZbo` | tinyint | ANO | ((2)) |  |
| 90 | `SlevaStavSkladu` | tinyint | ANO | ((2)) |  |
| 91 | `SlevaZbozi` | tinyint | ANO | ((2)) |  |
| 92 | `SlevaOrg` | tinyint | ANO | ((2)) |  |
| 93 | `IdTxtPenFak` | int | ANO |  |  |
| 94 | `Logo` | varbinary(MAX) | ANO |  |  |
| 95 | `KorekceSplatnoAuto` | int | NE | ((0)) |  |
| 96 | `KorekceSplatnoUziv` | int | NE | ((0)) |  |
| 97 | `NapocetProPT` | tinyint | NE | ((0)) |  |
| 100 | `DatPorizeni_D` | int | ANO |  |  |
| 101 | `DatPorizeni_M` | int | ANO |  |  |
| 102 | `DatPorizeni_Y` | int | ANO |  |  |
| 103 | `DatPorizeni_Q` | int | ANO |  |  |
| 104 | `DatPorizeni_W` | int | ANO |  |  |
| 105 | `DatPorizeni_X` | datetime | ANO |  |  |
| 106 | `DatZmeny_D` | int | ANO |  |  |
| 107 | `DatZmeny_M` | int | ANO |  |  |
| 108 | `DatZmeny_Y` | int | ANO |  |  |
| 109 | `DatZmeny_Q` | int | ANO |  |  |
| 110 | `DatZmeny_W` | int | ANO |  |  |
| 111 | `DatZmeny_X` | datetime | ANO |  |  |
| 113 | `KreditZustatek` | numeric(19,6) | ANO |  |  |
| 114 | `FaAktualizovano_D` | int | ANO |  |  |
| 115 | `FaAktualizovano_M` | int | ANO |  |  |
| 116 | `FaAktualizovano_Y` | int | ANO |  |  |
| 117 | `FaAktualizovano_Q` | int | ANO |  |  |
| 118 | `FaAktualizovano_W` | int | ANO |  |  |
| 119 | `FaAktualizovano_X` | datetime | ANO |  |  |
| 120 | `DatumNeupominani_D` | int | ANO |  |  |
| 121 | `DatumNeupominani_M` | int | ANO |  |  |
| 122 | `DatumNeupominani_Y` | int | ANO |  |  |
| 123 | `DatumNeupominani_Q` | int | ANO |  |  |
| 124 | `DatumNeupominani_W` | int | ANO |  |  |
| 125 | `DatumNeupominani_X` | datetime | ANO |  |  |
| 127 | `IDBankSpojPlatak` | int | ANO |  |  |
| 131 | `EORI` | nvarchar(17) | NE | ('') |  |
| 139 | `DruhDopravy` | tinyint | ANO |  |  |
| 140 | `DodaciPodminky` | nvarchar(3) | NE | ('') |  |
| 142 | `KorekceSplatnoUzivD` | int | NE | ((0)) |  |
| 143 | `RezimPenalizace` | tinyint | NE | ((0)) |  |
| 144 | `Penale` | tinyint | NE | ((0)) |  |
| 145 | `Partner` | nvarchar(7) | ANO |  |  |
| 146 | `PlatceDPH` | bit | NE | ((0)) |  |
| 147 | `IDSOZExpirace` | int | ANO |  |  |
| 148 | `NazevOkresu` | nvarchar(100) | NE | ('') |  |
| 149 | `NazevCastiObce` | nvarchar(100) | NE | ('') |  |
| 150 | `MestskaCast` | nvarchar(100) | NE | ('') |  |
| 151 | `KodAdrMista` | int | ANO |  |  |
| 154 | `NespolehPlatce` | tinyint | NE | ((3)) |  |
| 155 | `AktZWebuNespolehPlatce` | bit | NE | ((0)) |  |
| 156 | `AktZWebuZverejBankUcty` | bit | NE | ((0)) |  |
| 157 | `DatZverejNespolehPlatce` | datetime | ANO |  |  |
| 158 | `DatPoslOverNespolehPlatceSys` | datetime | ANO |  |  |
| 159 | `DatPoslOverNespolehPlatceUziv` | datetime | ANO |  |  |
| 160 | `ZajisteniDPHCisloFU` | nvarchar(20) | NE | ('') |  |
| 161 | `ZajisteniDPHJinyDuvodRuceni` | tinyint | NE | ((0)) |  |
| 162 | `ZajisteniDPHJinyDuvodRuceniDatZverej` | datetime | ANO |  |  |
| 163 | `DatZverejNespolehPlatce_D` | int | ANO |  |  |
| 164 | `DatZverejNespolehPlatce_M` | int | ANO |  |  |
| 165 | `DatZverejNespolehPlatce_Y` | int | ANO |  |  |
| 166 | `DatZverejNespolehPlatce_Q` | int | ANO |  |  |
| 167 | `DatZverejNespolehPlatce_W` | int | ANO |  |  |
| 168 | `DatZverejNespolehPlatce_X` | datetime | ANO |  |  |
| 169 | `DatPoslOverNespolehPlatceSys_D` | int | ANO |  |  |
| 170 | `DatPoslOverNespolehPlatceSys_M` | int | ANO |  |  |
| 171 | `DatPoslOverNespolehPlatceSys_Y` | int | ANO |  |  |
| 172 | `DatPoslOverNespolehPlatceSys_Q` | int | ANO |  |  |
| 173 | `DatPoslOverNespolehPlatceSys_W` | int | ANO |  |  |
| 174 | `DatPoslOverNespolehPlatceSys_X` | datetime | ANO |  |  |
| 175 | `DatPoslOverNespolehPlatceUziv_D` | int | ANO |  |  |
| 176 | `DatPoslOverNespolehPlatceUziv_M` | int | ANO |  |  |
| 177 | `DatPoslOverNespolehPlatceUziv_Y` | int | ANO |  |  |
| 178 | `DatPoslOverNespolehPlatceUziv_Q` | int | ANO |  |  |
| 179 | `DatPoslOverNespolehPlatceUziv_W` | int | ANO |  |  |
| 180 | `DatPoslOverNespolehPlatceUziv_X` | datetime | ANO |  |  |
| 181 | `ZajisteniDPHJinyDuvodRuceniDatZverej_D` | int | ANO |  |  |
| 182 | `ZajisteniDPHJinyDuvodRuceniDatZverej_M` | int | ANO |  |  |
| 183 | `ZajisteniDPHJinyDuvodRuceniDatZverej_Y` | int | ANO |  |  |
| 184 | `ZajisteniDPHJinyDuvodRuceniDatZverej_Q` | int | ANO |  |  |
| 185 | `ZajisteniDPHJinyDuvodRuceniDatZverej_W` | int | ANO |  |  |
| 186 | `ZajisteniDPHJinyDuvodRuceniDatZverej_X` | datetime | ANO |  |  |
| 187 | `PartnerICO` | nvarchar(20) | ANO |  |  |
| 188 | `LhutaSplatnostiDodavatel` | smallint | ANO |  |  |
| 189 | `Legislativa` | tinyint | NE | ((0)) |  |
| 190 | `KonsolidaceStatu` | bit | NE | ((0)) |  |
| 192 | `Logo_DatLen` | bigint | NE |  |  |
| 193 | `DICDPHVystup` | nvarchar(15) | ANO |  |  |
| 194 | `GPSZemepisnaSirka` | numeric(10,7) | ANO |  |  |
| 195 | `GPSZemepisnaDelka` | numeric(10,7) | ANO |  |  |
| 196 | `RUIANCislo` | nvarchar(50) | ANO |  |  |
| 197 | `RUIANPismeno` | nvarchar(10) | ANO |  |  |
| 198 | `JePartner` | bit | NE | ((0)) |  |
| 199 | `EmailSouhlas` | bit | NE | ((0)) |  |
| 200 | `IDKonOs` | int | ANO |  |  |
| 201 | `IDKateg` | int | ANO |  |  |
| 202 | `IDZdrojOsUdaju` | int | ANO |  |  |
| 203 | `Obrat` | numeric(19,2) | ANO |  |  |
| 204 | `PocetZam` | int | ANO |  |  |
| 205 | `PZ2Vstup` | bit | NE | ((0)) |  |
| 206 | `PZ2Vystup` | bit | NE | ((0)) |  |
| 207 | `PZ2PoradiVstup` | int | NE | ((0)) |  |
| 208 | `PZ2PoradiVystup` | int | NE | ((0)) |  |
| 209 | `DatumCasPoslSynchr` | datetime | ANO |  |  |
| 210 | `DatumCasPoslSynchr_D` | int | ANO |  |  |
| 211 | `DatumCasPoslSynchr_M` | int | ANO |  |  |
| 212 | `DatumCasPoslSynchr_Y` | int | ANO |  |  |
| 213 | `DatumCasPoslSynchr_Q` | int | ANO |  |  |
| 214 | `DatumCasPoslSynchr_W` | int | ANO |  |  |
| 215 | `DatumCasPoslSynchr_X` | datetime | ANO |  |  |
| 216 | `OmezeniZpracOU` | bit | NE | ((0)) |  |
| 217 | `FormaDopravy` | nvarchar(30) | ANO |  |  |
| 218 | `SKDPHPlatceNaZruseni` | bit | NE | ((0)) |  |
| 219 | `Agent` | bit | NE | ((0)) |  |
| 220 | `JeNovaVetaEditor` | bit | NE | ((0)) |  |
| 222 | `Firma` | nvarchar(255) | ANO |  |  |
| 224 | `AktOrgDleRegistru` | bit | NE | ((1)) |  |
| 226 | `LimitPlatHotovKontrola` | bit | NE | ((1)) |  |
| 227 | `HraniceMarze` | numeric(5,2) | ANO |  |  |
| 228 | `PouzitMarzeOdDo` | bit | NE | ((0)) |  |
| 229 | `UliceSCisly` | nvarchar(237) | NE |  |  |
| 231 | `PostovniAdresa` | nvarchar(255) | ANO |  |  |
| 232 | `Prijmeni` | nvarchar(100) | NE | ('') |  |
| 233 | `Jmeno` | nvarchar(100) | NE | ('') |  |
| 234 | `RodneCislo` | nvarchar(11) | NE | ('') |  |
| 235 | `DatumNarozeni` | datetime | ANO |  |  |
| 236 | `UcetPohledavky` | nvarchar(30) | ANO |  |  |
| 237 | `UcetZavazku` | nvarchar(30) | ANO |  |  |
| 238 | `UcetZalPrij` | nvarchar(30) | ANO |  |  |
| 239 | `UcetZalVyd` | nvarchar(30) | ANO |  |  |
| 240 | `DatumNarozeni_D` | int | ANO |  |  |
| 241 | `DatumNarozeni_M` | int | ANO |  |  |
| 242 | `DatumNarozeni_Y` | int | ANO |  |  |
| 243 | `DatumNarozeni_Q` | int | ANO |  |  |
| 244 | `DatumNarozeni_W` | int | ANO |  |  |
| 245 | `DatumNarozeni_X` | datetime | ANO |  |  |
| 246 | `UcetOstPohl` | nvarchar(30) | ANO |  |  |
| 247 | `UcetOstZavaz` | nvarchar(30) | ANO |  |  |
| 248 | `NastavDatSplatPocOdFV` | tinyint | NE | ((100)) |  |
| 249 | `NastavDatSplatPocOdFP` | tinyint | NE | ((100)) |  |
| 250 | `AktZWebuZverejBankUctySK` | bit | NE | ((0)) |  |
| 251 | `DatPoslOverBankySysSK` | datetime | ANO |  |  |
| 252 | `DatPoslOverBankySysSK_D` | int | ANO |  |  |
| 253 | `DatPoslOverBankySysSK_M` | int | ANO |  |  |
| 254 | `DatPoslOverBankySysSK_Y` | int | ANO |  |  |
| 255 | `DatPoslOverBankySysSK_Q` | int | ANO |  |  |
| 256 | `DatPoslOverBankySysSK_W` | int | ANO |  |  |
| 257 | `DatPoslOverBankySysSK_X` | datetime | ANO |  |  |
| 258 | `AutoUPOMPF_JakaMena` | tinyint | NE | ((0)) |  |
| 259 | `AutoUPOMPF_Mena` | nvarchar(3) | ANO |  |  |
| 260 | `AutoUPOMPF_Upominat` | bit | NE | ((1)) |  |
| 261 | `AutoUPOMPF_UpomPo` | tinyint | NE | ((0)) |  |
| 262 | `AutoUPOMPF_UpomPoDnu` | smallint | ANO |  |  |
| 263 | `AutoUPOMPF_UpomOd` | tinyint | NE | ((0)) |  |
| 264 | `AutoUPOMPF_UpomOdCastka` | numeric(19,6) | ANO | ((0)) |  |
| 265 | `AutoUPOMPF_Penalizovat` | bit | NE | ((1)) |  |
| 266 | `AutoUPOMPF_PenalPo` | tinyint | NE | ((0)) |  |
| 267 | `AutoUPOMPF_PenalPoDnu` | smallint | ANO |  |  |
| 268 | `AutoUPOMPF_PenalOd` | tinyint | NE | ((0)) |  |
| 269 | `AutoUPOMPF_PenalOdCastka` | numeric(19,6) | ANO | ((0)) |  |
| 270 | `AresDatumAktualizaceRegistru` | datetime | ANO |  |  |
| 271 | `VstupniCenaDod` | tinyint | NE | ((100)) |  |
| 272 | `VstupniCenaOdb` | tinyint | NE | ((100)) |  |
| 273 | `AVAReferenceID` | nvarchar(40) | NE | (CONVERT([nvarchar](36),CONVERT([uniqueidentifier],newid()))) |  |
| 274 | `AVAExternalID` | nvarchar(255) | NE | ('') |  |
| 275 | `SystemRowVersion` | timestamp | NE |  |  |
| 276 | `AresDatumAktualizaceRegistru_D` | int | ANO |  |  |
| 277 | `AresDatumAktualizaceRegistru_M` | int | ANO |  |  |
| 278 | `AresDatumAktualizaceRegistru_Y` | int | ANO |  |  |
| 279 | `AresDatumAktualizaceRegistru_Q` | int | ANO |  |  |
| 280 | `AresDatumAktualizaceRegistru_W` | int | ANO |  |  |
| 281 | `AresDatumAktualizaceRegistru_X` | datetime | ANO |  |  |
| 282 | `SystemRowVersionText` | nvarchar(16) | ANO |  |  |
| 283 | `DnyToleranceScontaFaV` | int | ANO |  |  |
| 284 | `AVAOutputFlag` | tinyint | NE | ((0)) |  |
| 285 | `AVASentDate` | datetime | ANO |  |  |
| 287 | `AVASentDate_D` | int | ANO |  |  |
| 288 | `AVASentDate_M` | int | ANO |  |  |
| 289 | `AVASentDate_Y` | int | ANO |  |  |
| 290 | `AVASentDate_Q` | int | ANO |  |  |
| 291 | `AVASentDate_W` | int | ANO |  |  |
| 292 | `AVASentDate_X` | datetime | ANO |  |  |
| 293 | `AutoUPOMPF_UpomDoDnu` | smallint | ANO |  |  |
| 294 | `AVAReceivedDate` | datetime | ANO |  |  |
| 295 | `Logo_BGJ` | nvarchar(6) | ANO |  |  |
| 296 | `AVAReceivedDate_D` | int | ANO |  |  |
| 297 | `AVAReceivedDate_M` | int | ANO |  |  |
| 298 | `AVAReceivedDate_Y` | int | ANO |  |  |
| 299 | `AVAReceivedDate_Q` | int | ANO |  |  |
| 300 | `AVAReceivedDate_W` | int | ANO |  |  |
| 301 | `AVAReceivedDate_X` | datetime | ANO |  |  |
| 302 | `UcetZalohyZakladFP` | nvarchar(30) | ANO |  |  |
| 303 | `UcetZalohyZakladFV` | nvarchar(30) | ANO |  |  |

## Cizí klíče (declared)

- `NadrizenaOrg` → [`TabCisOrg`](TabCisOrg.md).`CisloOrg` _(constraint: `FK__TabCisOrg__NadrizenaOrg`)_
- `DruhCinnosti` → `TabDruhCinnosti`.`ID` _(constraint: `FK__TabCisOrg__DruhCinnosti`)_
- `CenovaUroven` → `TabCisNC`.`CenovaUroven` _(constraint: `FK__TabCisOrg__CenovaUroven`)_
- `IDSOZsleva` → `TabSoz`.`ID` _(constraint: `FK__TabCisOrg__IDSOZsleva`)_
- `IDSOZnazev` → `TabSoz`.`ID` _(constraint: `FK__TabCisOrg__IDSOZnazev`)_
- `OdpOs` → [`TabCisZam`](TabCisZam.md).`ID` _(constraint: `FK__TabCisOrg__OdpOs`)_
- `AutoUPOMPF_Mena` → `TabKodMen`.`Kod` _(constraint: `FK__TabCisOrg__AutoUPOMPF_Mena`)_
- `IDBankSpojeni` → `TabBankSpojeni`.`ID` _(constraint: `FK__TabCisOrg__IDBankSpojeni`)_
- `CenovaUrovenNakup` → `TabCisNC`.`CenovaUroven` _(constraint: `FK__TabCisOrg__CenovaUrovenNakup`)_
- `IdTxtPenFak` → `TabTxtUpo`.`ID` _(constraint: `FK__TabCisOrg__IdTxtPenFak`)_
- `IDKateg` → `TabKategOrg`.`ID` _(constraint: `FK__TabCisOrg__IDKateg`)_
- `IDKonOs` → `TabCisKOs`.`ID` _(constraint: `FK__TabCisOrg__IDKonOs`)_
- `IDZdrojOsUdaju` → `TabZdrojeOsUdaju`.`ID` _(constraint: `FK__TabCisOrg__IDZdrojOsUdaju`)_
- `UcetOstPohl` → `TabCisUct`.`CisloUcet` _(constraint: `FK__TabCisOrg__UcetOstPohl`)_
- `UcetOstZavaz` → `TabCisUct`.`CisloUcet` _(constraint: `FK__TabCisOrg__UcetOstZavaz`)_
- `Jazyk` → `TabJazyky`.`Jazyk` _(constraint: `FK__TabCisOrg__Jazyk`)_
- `Mena` → `TabKodMen`.`Kod` _(constraint: `FK__TabCisOrg__Mena`)_
- `Region` → `TabRegion`.`Cislo` _(constraint: `FK__TabCisOrg__Region`)_
- `IdZeme` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisOrg__IdZeme`)_
- `UcetPohledavky` → `TabCisUct`.`CisloUcet` _(constraint: `FK__TabCisOrg__UcetPohledavky`)_
- `UcetZalPrij` → `TabCisUct`.`CisloUcet` _(constraint: `FK__TabCisOrg__UcetZalPrij`)_
- `UcetZalohyZakladFP` → `TabCisUct`.`CisloUcet` _(constraint: `FK__TabCisOrg__UcetZalohyZakladFP`)_
- `FormaDopravy` → `TabFormaDopravy`.`FormaDopravy` _(constraint: `FK__TabCisOrg__FormaDopravy`)_
- `UcetZalVyd` → `TabCisUct`.`CisloUcet` _(constraint: `FK__TabCisOrg__UcetZalVyd`)_
- `UcetZalohyZakladFV` → `TabCisUct`.`CisloUcet` _(constraint: `FK__TabCisOrg__UcetZalohyZakladFV`)_
- `UcetZavazku` → `TabCisUct`.`CisloUcet` _(constraint: `FK__TabCisOrg__UcetZavazku`)_
- `IDBankSpojPlatak` → `TabBankSpojeni`.`ID` _(constraint: `FK__TabCisOrg__IDBankSpojPlatak`)_
- `FormaUhrady` → `TabFormaUhrady`.`FormaUhrady` _(constraint: `FK__TabCisOrg__FormaUhrady`)_
- `IDSOZExpirace` → `TabSoz`.`ID` _(constraint: `FK__TabCisOrg__IDSOZExpirace`)_

## Indexy

- **PK** `PK__TabCisOrg__CisloOrg` (CLUSTERED) — `CisloOrg`
- **UNIQUE** `UQ__TabCisOrg__ID` (NONCLUSTERED) — `ID`
- **UNIQUE** `UQ__TabCisOrg__AVAReferenceID` (NONCLUSTERED) — `AVAReferenceID`
- **INDEX** `IX__TabCisOrg__AVAExternalID` (NONCLUSTERED) — `AVAExternalID`
