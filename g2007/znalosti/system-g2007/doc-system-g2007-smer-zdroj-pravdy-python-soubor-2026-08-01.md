# SMĚR (Marti, 1.8.2026, potvrzeno a UZAVŘENO 2.8.2026): g2007.python + g2007.soubor jsou zdroj pravdy — router.py a staticke soubory se z nich VYPRAZDNUJI

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# SMĚR (Marti, 1.8.2026, potvrzeno a UZAVŘENO 2.8.2026): g2007.python + g2007.soubor jsou zdroj pravdy — router.py a staticke soubory se z nich VYPRAZDNUJI

**Toto je zavazny smer od Martiho pro VSECHNY Claude instance (Claude-23, Claude-26/Peta,
Claude-28/Jirka, dalsi) i lidi, ne jen informativni poznamka.** Rozsiruje a nahrazuje uzsi
`doc-system-strategie-cil-migrace-router-py-g2007-python-schvaleno` (ktery resil jen
banner-doktrinu pro g2007.python) o jasny, obecny prikaz smeru pro OBA systemy.

## UZAVIRACI DOLOZKA (Marti, 2.8.2026) — cti jako prvni, plati bez vyjimky

Marti 2.8.2026 vyslovne potvrdil a uzavrel smer nize jako ZAVAZNY POKYN, ne jen doporuceni:

1. **Stary system (primy zapis/editace v router.py, primy zapis statickych souboru na
   disk mimo g2007.soubor) se DAL NEROZVIJI.** Zadna Claude instance ani clovek nema
   pridavat novou logiku primo do router.py nebo novy staticky obsah primo na disk.
   Vyjimka jsou VYSLOVNE jen tenke delegate handlery (par radku: precti req, over
   auth, zavolej `erp_registry.call(kod, ...)`, zabal odpoved) — cela business logika
   patri do `g2007.python`.
2. **Kdokoli neco edituje, opravuje, nebo chce nasadit (deploy) a pouzivat, MUSI si to
   sam nejdriv migrovat do g2007 systemu** (g2007.python pro backend funkce/endpointy,
   g2007.soubor pro web/staticke soubory), stejnym overenym vzorem jako dosavadni
   migrace (viz `doc-system-g2007-migrace-python-soubor-stav-2026-08-01`) — sobestacny
   skript (vsechny zavislosti inlinovane, protoze `erp_registry.call` bezi v prazdnem
   exec namespace), vlozit jako `stav_zivota='navrzeno'`, over hash/logiku/pripadne
   `selftest_compare`, a teprve pak (po review, u citliveho kodu spolecne s Martim)
   aktivovat na `stav_zivota='active'`.
3. **Nikdo nema pouzivat/rozvijet stary primy zapis "protoze je to rychlejsi" nebo
   "jen mala oprava".** I mala oprava existujici funkce v router.py = prilezitost a
   povinnost ji rovnou migrovat, ne opravit na miste a nechat v ne-zdroji-pravdy.
4. **Cil zustava: postupne VYPRAZDNIT router.py a staticke soubory smerem do DB.**
   Kazda instance/clovek, ktery ma na starosti nejakou oblast, ji prubezne migruje
   misto cekani, az to udela nekdo jiny.

Toto neni zmena smeru z 1.8.2026 nize — je to jeho vyslovne potvrzeni a uzavreni jako
zavazneho pravidla pro VSECHNY (Marti, 2.8.2026, po dokonceni pripravy cele rodiny
`mzdy_generuj` — viz stav nize a `g2007.denik` id 5-6).

## Co to znamena konkretne

1. **Zdroj pravdy uz NENI router.py ani staticke soubory na disku primo editovane.**
   Zdroj pravdy je DB radek — `g2007.python` pro backend funkce, `g2007.soubor` pro
   web/staticke soubory (HTML/JS/CSS). Router.py a disk jsou jen odvozene/generovane
   z DB (delegate handler resp. materializovany export). Kdo pise/opravuje kod primo v
   router.py nebo primo edituje static soubor na disku bez pruchodu pres DB, jde proti
   smeru.

2. **Nova prace jde VZDY primo pres novy system, ne pres router.py/disk.** Novy
   endpoint/funkce = rovnou "sobestacny" skript do `g2007.python` (viz vzor a prikazy
   nize) + tenky delegate v router.py. Novy staticky obsah = rovnou `g2007.soubor`
   (`@@G2007SOUBOR`), ne novy soubor rovnou na disku mimo system.

3. **Existujici kod se aktivne stehuje ven z router.py.** Kazdy, kdo ma na starosti
   nejakou cast (dochazka/mzdy uz hotovo — viz nize), by mel postupne prochazet SVOJI
   oblast v router.py a migrovat ji do g2007.python stejnym overenym vzorem, ne cekat,
   az to nekdo udela za nej. Cil neni "pridat par funkci do g2007", cil je postupne
   VYPRAZDNIT router.py smerem do DB.

4. **Jak presne (technicky detail + oba zname incidenty s poucenim):** viz
   `doc-system-g2007-migrace-python-soubor-stav-2026-08-01` — obsahuje vzor
   "sobestacneho" skriptu, aktivacni 2-krokovy postup, prikazy `@@G2007SOUBOR` /
   `@@G2007SESTAV` / `@@G2007EXPORT` / `@@G2007PUBLISH`, a hlavne DVA REALNE
   INCIDENTY (tichy pad mezer ve schvalovaci fronte u g2007.python; vypadek /mobile
   z naivniho JS-fragment joinu u g2007.soubor) a jak se jim priste vyhnout.

## Rychla pravidla, ktera musi znat kazdy, kdo se do tohoto pousti

- Pred aktivaci (`stav_zivota='active'`) cehokoli citliveho: over hash posledni verze
  primo v `g2007.python_historie` / analogicky u g2007.soubor, ne jen "vypada to OK".
- INSERT/UPDATE VYHRADNE do `g2007.python` bezi autonomne (bez banneru). Totez plati
  pro `g2007.soubor` pres `@@G2007SOUBOR`/`@@G2007SESTAV`/`@@G2007PUBLISH`. Mazani
  (DELETE/TRUNCATE/ALTER) zustava VZDY gated — schvaluje Marti v banneru.
  `device_bash`/primy zapis na disk soubory NEMAZE (bridge to neumoznuje) — na
  fyzicke smazani/vycisteni disku se pouziva git (add/commit/push pres deploy most)
  nebo se pozada Marti o rucni zasah.
- Zapis do znalosti (vcetne aktualizace tohoto dokumentu) jde VYHRADNE pres
  `@@G2007ADD <oblast> <slug> | <nadpis>` — nikdy raw INSERT, nikdy `docs/Z_*.md`.
- Prace se zaznamenava do `g2007.denik`, aby dalsi instance/clovek videl, co uz kdo
  dela, aniz by musel cist cely chat.
- **Citlive/produkcni aktivace (napr. cokoli z okruhu mezd, cokoli s realnym
  penezenim/MSSQL dopadem) se NIKDY neaktivuje samostatne jednou instanci.** Priprava
  (`stav_zivota='navrzeno'`) je autonomni, ale prechod na `'active'` vyzaduje spolecne
  review s Martim — plati bez vyjimky.

## Stav k 2.8.2026 (co uz jede novym systemem)

- **g2007.python:** dochazka + mzdy (Faze A-F) — vcetne cele rodiny `mzdy_generuj`
  (hlavni endpoint generovani mezd na cloud Heliosu) nyni KOMPLETNI a AKTIVNI (`stav_zivota='active'`):
  `lm_engine`, `mzdy_worker_sql`, `mzdy_refresh_zrcadla`, `mzdy_benefity_apply`,
  `mzdy_generuj` — vsech 5 AKTIVOVANO 2.8.2026 (`stav_zivota='active'`, po spolecnem
  review s Martim; `mzdy_generuj` aktivovano 2.8. v 08:38 SELC, zbytek rodiny 1.-2.8.),
  overeno primo v `g2007.python` (C24 Kristy, 3.8.2026). Generovani mezd
  (`/app/mzdy/generuj`) tak bezi zive na novem systemu jako tenky delegate, funkcne
  1:1 beze zmeny logiky. Vedle toho
  60+ jiz aktivnich radku z drivejsich fazi (att_*/mzdy_* delegaty, mzdy_c_smlouvy,
  mzdy_status_check, mzdy_vyplatnice a dalsi). Pri migraci `mzdy_generuj` nalezen a
  1:1 preziti (NEOPRAVENO zamerne) latentni bug puvodniho kodu: blok "jednatelske
  stravne" pouziva nedefinovana jmena (`_JEDNATELE_CISLA` aj.) a v produkci vzdy tise
  spadne do warningu — detail viz docstring skriptu `mzdy_generuj` a `g2007.denik`
  id 6; oprava je vedome samostatne rozhodnuti Martiho, ne soucast migrace. Zbytek
  router.py (mimo poptavky/nabidky/kalkulace, ktere maji vlastni `EC_GenPoptavku`
  cestu a NEJSOU soucasti teto migrace) je VOLNY k postupnemu prevzeti dalsimi
  instancemi/lidmi.
- **g2007.soubor:** `/mobile` kompletne rozlozeny na ~28 zdroj fragmentu + sestaveny
  artefakt `mobile.html`. Sandbox `/mobile2` byl smazan (byl bajt-identicky s
  `/mobile`, zadna unikatni logika se neztratila — nova logika uz je v `/mobile`).
  `index.html`/`marti.html`/`foto.html`/`overit.html`/`vyroba.html` jsou v
  g2007.soubor zatim jen jako holé artefakty bez zdroj-rozkladu — dalsi kandidati.

**Shrnuti pro kazdeho, kdo cte tenhle dokument: pokud pracujes na necem v router.py
nebo na statickem web souboru, NEJDRIV zkontroluj, jestli uz to nema byt (nebo neni)
v g2007.python/g2007.soubor — a pokud tam jeste neni, MIGRUJ TO TAM misto pridavani
dalsiho kodu do router.py/na disk primo. Toto neni volitelne doporuceni, je to
zavazny pokyn Martiho (1.8. a potvrzeno 2.8.2026).**

