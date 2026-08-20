# Vyhodnoceni zakazek: stav k 4.8.2026 (co hotovo, na cem to stoji, pasti)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Vyhodnoceni zakazek - stav k 4.8.2026

Zapsal C28 (Jirka) 4.8.2026, vse overeno ctenim z DB/Centraly.
Navazuje na [doc-vyroba-vyhodnoceni-zakazek], [doc-vyroba-zak-zakazka-meta].

## SMER (Jirka 4.8.)
Data z `tenant.oz_zakazky` (zrcadlo) + `tenant.zakazka_meta`. **Zadne zdvojovani tabulek** - Jirka odmitl
variantu "zrcadlo + pracovni tabulka": *"pak reknem, ze uz v centrale se to delat nebude"*. Cil = jen STRATEGIE.

## HOTOVO 4.8.
- **oz_zakazky + 11 kalkulacnich sloupcu** z TabZakazka_EXT (#1739 ALTER, #1740 uprava dotazu v
  `tenant.oz_mirror_def.sql_mssql`). Po syncu 09:30: KalkHodiny 3747, DatumVyhodnoceni 3655,
  GarantCisloZam 3459, **sefmonterCislo 3295** (dosud jen JMENEM = neparovatelne), VyhodnoceniUzavreno 4444.
  Nizka cisla u KalkHodVyroba 19/41 a SrazkaSerie 61 NEJSOU chyba - v Centrale se plni vyjimecne.
- **vyroba_cinnost.nepocitat_do_hodnoceni** (#1742) dle EC_DilnaCinnosti - prosel jsem 45 cinnosti,
  priznak ma **JEDINA: Garant (EC 53)**.
- **ec.vyhodnoceni_konstanty** (#1743): premie 130 / srazka 30 / rezerva 1,15 + historicka premie 100
  (2020-07-12 az 2021-10-06). Sedi se zkusebni VR10704.

## SAZBA = SUPERHRUBA (dolozeno)
EC_Dochazka.Kc_Hod_FinPodm = EC_FinZamPodminky.ZakladZaHod = SuperhrHodsFK. Cervenec: os.536 345,98 vs
hruba 247,13; os.488 271,95 vs 194,25; os.483 253,45 vs 181,03 -> **pomer presne 1,4** (tentyz koeficient
uz je v portovane ec.vyhodnoceni_uzavrit). Potvrzeni od cloveka zatim NENI - odeslano Kristy 4.8. 10:56.

## STRATEGIE UMI SAZBU SPOCITAT SAMA
suma mesicnich `tenant.wage_component` (kind='monthly') / `tenant.engagement.fond_mesic_h` = hruba hodinova;
x 1,4 = superhruba. Overeno na 4 lidech - sedi s Centralou NA HALIR. Fond 174 h u 77 lidi, vyjimky 152,25
a 11 h, u 1 cloveka fond PRAZDNY (tam by vypocet spadl). `helios_wage_snapshot` NEPOUZIVAT (mesicni castky,
snimek z 11.6.2026).

## ZDROJE V DB_EC (dohledano)
| nase | zdroj | radku | realnych | smeti |
|---|---|---|---|---|
| ec.vyhodnoceni_zakazka | EC_VyhodnoceniZak_KonstantyKZak | 1866 | 1863 | 3 |
| ec.vyhodnoceni_osoba | **EC_TempVyhodnoceniZak** | 15313 | 15306 | 7 |
| ec.zakazky_finance_zam | EC_ZakazkyFinanceZam | 23479 | 23479 | 0 |
Zdroj pro osoby NENI EC_ZakazkyHodnoceni (jine sloupce). KonstantyKZak NEJSOU sazby, ale HLAVICKY vyhodnoceni.
Duplicity overeny: **zadne** - co vypadalo jako duplicita, jsou prazdne radky. Klice: hlavicka `cislo_zakazky`,
osoby a vyplaty `(cislo_zakazky, cislo_zam)`.

## ⚠️ PAST: zrcadlo nesmi plnit tabulku, do ktere modul zapisuje
`oz_mirror.fill()` r.129 dela **TRUNCATE + INSERT**. `ec.vyhodnoceni_zakazka` je ale tabulka, do ktere modul
SAM zapisuje (prepocet/uzavrit) - klasicke zrcadlo by vypocty pri nejblizsim behu (~30 min) SMAZALO, tise.
Reseni = rizeny upsert na klic + ochrana radku `zdroj='strategie'`, ne truncate.

## ⚠️ PAST: sazba musi byt snapshot u radku
Centrala uklada sazbu k zaznamu pri vzniku. Os. 531 (Jungmann) ma sazbu v cervenci, ale u nas je uz
neaktivni bez pomeru -> zpetny dopocet by nespocital nic. Jirka odsouhlasil: **ukladat sazbu k radku
rozpadu prace pri vzniku.**

## SCHVALENO MARTI-AI (msg 12044)
UNIQUE dle klicu vyse (partial, WHERE cislo neni prazdne) · **oba sloupce `zdroj` I `uzamceno`** (zdroj =
odkud radek prisel a co smi prenos mazat; uzamceno = nedotknutelna historie) · import po letech s overenim ·
historie `uzamceno=true` (stare mesice se NESMI prepocitat).

## CEKA
#1747 (sloupce+UNIQUE) · souhlas s prenosem 23479 vyplat · potvrzeni superhrube - vse na Kristy (mail 4.8.
10:56, log 98). Marti Pasek 4.8. neodpovedel na nic. Pak: import po letech + porovnani naseho vypoctu proti
Centrale na tisicich zakazek (dnes overena 1 = VR10704).

## PORAD PLATI ZE STARSIHO SOUPISU
Neni kam ulozit (jadro ma jen 'edit', gridy 'select-detail', zadna save operace) · chybi obrazovka pro zapis
sefmontera do zakazka_meta · nikde se nezapisuje KDO spustil uzaverku vyplat · akci muze spustit kdokoli
z 19 lidi s ERP pristupem (menu to jen schovava).

## SYNC ZAKAZEK
`oz_sync_all` bezi ~30 min (4.8. behy 08:24, 08:56, 09:30 - ne 10 min, jak rika starsi dokumentace).
Rucne: ERP -> ⚙ Ops akce -> oz_sync_all. Zrcadleny SELECT se upravuje v `tenant.oz_mirror_def.sql_mssql`,
NE ve fw.data_set (ten uz je repointovany na PG).

