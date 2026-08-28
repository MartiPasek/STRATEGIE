# Odvozy: stav k 28. 8. 2026 a co konkretne brani presunu potvrzovani do mobilu

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> Navazuje na [[doc-dochazka-odvozy-potvrzovani-stoji-od-22-7-2026]] (rozbor pricin z 25. 8.)
> a [[doc-dochazka-vypnuti-centrala-tablet-tlacitka]]. Tady je **cerstve mereni a soupis
> prekazek** pro rozhodnuti, jak potvrzovani presunout do mobilu (rozhodnuti Kristy + Jirky
> z 30. 7. 2026: terminal se neobnovuje).

## Mereni 28. 8. 2026 (cteno primo z DB_EC)

| mesic 2026 | naplanovano | nepotvrzeno |
|---|---|---|
| leden-kveten | 121 | 2 |
| cerven | 23 | 2 |
| **cervenec** | 30 | **9** |
| **srpen** | 36 | **36 (ani jeden)** |

- **49 nepotvrzenych odvozu, ktere uz probehly** (rano 28. 8.; o dve hodiny driv jich bylo 47 -
  **cislo roste kazdy den**, uvadej vzdy s datem a hodinou mereni).
- 48 ruznych zakazek, z toho **11 do zahranici** (D, H), 0 blokovanych.
- Nejstarsi dluzny 26. 1. 2026, posledni potvrzeni **21. 7. 2026 14:02**.
- Navic 15 odvozu naplanovanych do budoucna (ty potvrzene byt nemaji).

## Kdo potvrzoval (cela historie od 2022)

| kdo | potvrzeni | naposledy |
|---|---|---|
| Jaroslav Svenda (os. 488, user 67) | 1 034 | 21. 7. 2026 |
| Martin Nosek (os. 425, user 52) | 249 | 20. 7. 2026 |
| Dusan Havlat (os. 105, user 41) | 21 | 9/2025 |
| dalsi ctyri | 23 dohromady | vetsinou 2022-2023 |

**Dva lide udelali 97 % vsech potvrzeni** a oba prisli o tablet tyz den (22. 7. 2026).

## Ctyri konkretni prekazky presunu do mobilu

1. **Mobil neumi potvrdit.** Existuje jen ctecí obrazovka (`app_vyroba_odvozy`) a poznamky
   (`app_vyroba_odvoz_pozn_list` / `_create`). **Zadna ziva funkce nezapisuje `DatumOdvezeni`.**
2. **Zrcadlo nenese stav potvrzeni.** `tenant.vyroba_odvoz` ma sloupce
   `tenant_id, ext_id, cislo_zakazky, datum_odvozu, poznamka, adresa, synced_at` - **zadny
   `datum_odvezeni` ani `odvoz_potvrdil`**, takze appka ani neumi ukazat, co je hotove.
3. **Okno stahovani je -7 dni.** `_sync_odvozy_from_ec` (jadro) tahá z pohledu
   `ECv_Vytizeni_Odvozy` pres EUROSOFT MCP jen `DatumOdvozu >= dnes-7`. K 28. 8. je v zrcadle
   25 radku. **Z 49 dluznych by jich mobil videl jen 8, zbylych 39 je mimo okno.**
4. **Lide, kteri to delali, na obrazovku nevidi.** `app_vyroba_odvozy` pousti dovnitr
   `_VYROBA_MANAGERS = {16, 41, 85}` (Hladikova, Havlat, Honal) + rodice.
   **Svenda ani Nosek mezi nimi nejsou.**

## Pasti v potvrzovaci procedure Centraly

`EC_DopravaZakaznikovi_PotvrzeniOdvozu`:
- je to **prepinac** (`DatumOdvezeni = IIF(DatumOdvezeni is null, GETDATE(), NULL)`, stejne
  `OdvozPotvrdil`) - druhy stisk potvrzeni zrusi vcetne toho, kdo ho udelal,
- **notifikace odejde i pri zruseni**, porad s textem "byla prave oznacena jako odvezena",
- **prijemci natvrdo v kodu**: LoginId `ZDivis` a `Dusan`.

⚠️ **NEMERITELNE:** jestli se ruseni potvrzeni nekdy realne pouzivalo. Archiv
`EC_DopravaZakaznikovi_Archiv` ma u tech radku prazdne hodnoty a mnoho zaznamu se stejnym
`DatZmeny`, takze `LAG` pres nej dava nesmyslna cisla. *(Pri prvnim pokusu z nej vyslo
"455 pripadu ruseni" - pri kontrole na konkretnim zaznamu se ukazalo, ze to cislo neznamena
nic. Neuvadej ho.)*

## Beistellung

Spadl tyz den a stejnym mechanismem. **V mobilu neni vubec** (ani ke cteni). Neni to
dochazkova vec - meni stav zakazky `tabZakazka_ext._StavBeistellung`.
Stav k 28. 8. 2026: Neni 5 591 · Kompletne dodan 97 · Castecne dodan 10 · Nedodan 1.
⚠️ **Zmeny se nikam neloguji** (procedura `EC_Zakazky_NastavBeistellung` parametr "kdo" prijima,
ale nepouziva), takze **vypadek u Beistellungu nejde zmerit vubec**.

## Co ceka na rozhodnuti cloveka (k 28. 8. 2026 neuzavreno)

1. kdo smi potvrzovat (Svenda + Nosek? dnesni tri? role v org strukture?),
2. jednosmerne potvrzeni, nebo prepinac jako v Centrale,
3. maji chodit notifikace ZDivis/Dusan (volat proceduru) nebo zapisovat primo,
4. co s 49 dluznymi - dopotvrdit zpetne (pod cim jmenem?) nebo hlidat az od ted;
   u 39 z nich by se muselo rozsirit okno stahovani,
5. Beistellung resit spolu s odvozy, nebo zvlast.

Podklad pro Jirku sepsan 28. 8. 2026 (soubor na jeho plose, mimo repo i mimo G2007 -
obsahuje jmenovity seznam zakazek).

