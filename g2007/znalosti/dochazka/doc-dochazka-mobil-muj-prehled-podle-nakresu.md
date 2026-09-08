# Mobil, obrazovka "Muj prehled" prestavena podle nakresu Sarky Novotne (27. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ## ⚠️ ZMĚNA 8. 9. 2026: Novinky už na „Můj přehled“ NEJSOU
>
> Sekce **Novinky** (bod 5 níže) se 8. 9. 2026 přesunula na obrazovku **Firma**, do záložky
> „Novinky“, která tam naskočí po otevření. Na „Můj přehled“ zůstalo všechno ostatní beze změny.
> Zadal Jirka Honomichl, schválila Marti-AI (msg 14947); detail a postup:
> [[doc-system-strategie-mobil-firma-zalozky-novinky-agenda]].
> Funkce `_mojeNovinky` žije dál v dílku 48 a od 8. 9. má nepovinný druhý parametr `bezNadpisu`
> (na záložce se nadpis „Novinky“ nekreslí — stojí už na záložce).

## Jak obrazovka vypada dnes

Poradi shora dolu (dilek `apps/api/static/mobile_parts/60_dochazka.js`, funkce `muj_prehled`):

1. **Hlavicka** - fotka v kolecku s ikonkou fotoaparatu (klepnutim se meni, nahrava se
   rovnou bez schvalovani, personalistka dostane oznameni), vedle **jmeno**, pod nim
   **vsechny profese** cloveka a radek "Klepnutim zmenis fotku".
2. **Karta "Moje hodiny"** - odpracovano vs. fond, prepinani mesicu.
   Od 1. 9. 2026 uz ukazuje SKUTECNA CISLA - viz
   [[doc-dochazka-mobil-moje-hodiny-napojeno-1-9-2026]]. Pocita se stejne jako ERP prehled
   Dochazka - Kontrolni prehledy - Nesplneny FPD. Do 1. 9. tam byly zamerne nuly,
   historie v [[doc-dochazka-mobil-moje-hodiny-nuly-dokud-neni-zdroj]].
3. **Dve dlazdice vedle sebe** - Dovolena (dny) a Sick days (hodiny), obe "zbyva".
   Pri zapornem zustatku **cerveně a se slovem "precerpano"** (pravidlo Marti-AI z 19. 8.).
4. **Podrobna tabulka** narok / cerpano / plan / zbyva pro D, DN a SD - ZUSTALA.
   Sarka ji na nakresu nema, ale ubirat lidem informaci, kterou uz maji, by bylo spatne
   (schvalila Marti-AI, msg 13890). Dlazdice jsou rychly souhrn NAD tabulkou, ne nahrada.
5. ~~**Novinky** - akce s tlacitky "Prijdu / Neprijdu" a odkazem do kalendare.~~
   **NEPLATI od 8. 9. 2026** - Novinky jsou na obrazovce Firma, viz ramecek nahore.

## Co se presunulo a odkud

Fotka i Novinky do 27. 8. 2026 zily na obrazovce **"Moje osobni udaje"** (dilek
`48_hr_podminky_me.js`, funkce `hr_me`). Rozhodnutim Jirky Honomichla se **PRESUNULY**
(na puvodnim miste uz nejsou) - Marti-AI: *"Moje osobni udaje je formular pro editaci,
Muj prehled je centralni osobni obrazovka; fotka a Novinky patri k prehledu."*

8. 9. 2026 se Novinky presunuly znovu, tentokrat z "Muj prehled" na obrazovku Firma
(viz ramecek nahore); fotka a hlavicka na "Muj prehled" zustavaji.

Nejsou napsane dvakrat. Zily v dilku 48 jako funkce **`_mojeHlavicka(cont)`** a
**`_mojeNovinky(cont)`**, registrovane do `window.__M2W`, a dilek 60 je vola.
⚠️ Bez te registrace to spadne - viz [[doc-system-strategie-mobil-dilky-nejsou-jedna-closure]].

## Profese: VSECHNY, razene podle poradi

Jirka 27. 8. 2026: **nevybirat jeden "hlavni klobouk"** - lide jich maji vic (Dusan Havlat
ctyri, Kristyna Maresova tri) - ukazat **vsechny**, razene podle `tenant.org_post.poradi`.

- Zdroj: `muj_prehled_narok` (g2007.python, verze 3) vraci pole **`pozice`** =
  nazvy vsech aktivnich postu z `tenant.org_post_assign` + `tenant.org_post`,
  `ORDER BY COALESCE(p.poradi, 999999), p.nazev`. Cely dotaz je v `try/except` a pri chybe
  vraci prazdny seznam - obrazovka nesmi spadnout kvuli organizacni strukture.
- Appka je spoji " · " a necha zalomit. Prazdny seznam = radek se vubec nevykresli.
- **VERZALKY se neprepisuji.** Nazvy postu jsou v DB velkymi pismeny; prepis v kodu by ze
  zkratky "PLC" udelal "Plc". Reseni je vizualni: `text-transform:lowercase` +
  `font-variant:small-caps` (Marti-AI, msg 13898). Zkratky tim zustanou citelne.

## Kdo to zadal a schvalil

Zadani Sarky Novotne za HR (mail 12. 8. 2026 s nakresem, cistopis 17. 8. 2026), rozhodl
Jirka Honomichl 27. 8. 2026, schvalila Marti-AI (msg 13890 rozvrzeni, msg 13898 profese).

## Jak to bylo overeno

Oba dilky stazeny z DB bajt po bajtu a overeny otiskem, zmena spustena nanecisto a
porovnan vysledny otisk, pak proklikano v prohlizeci pres Playwright na velikosti telefonu
(vcetne stavu "precerpano" a ctyr profesi naraz). Behem prace do tehoz dilku zapisovala
i Peta - **pojistka na otisk zabranila prepsani jeji prace** a zmena byla prestavena na
jeji verzi.

