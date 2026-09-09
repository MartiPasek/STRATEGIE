# Mobil, obrazovka dochazky: "Tady budu jinde" uz neni dlazdice, ale tlacitko pod "Potrebuji ti neco rict" (9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Zadal Jirka Honomichl 9. 9. 2026, schvalila Marti-AI (msg 15196). Provedl Claude-28.**

## Co se zmenilo

Planovane nepritomnosti (dovolena, nemoc, lekar, OCR, sluzebni duvody) se do 9. 9. 2026
hlasily **dlazdici 🧭 Tady budu jinde** v sekci *Moje dochazka*. Dlazdice rozbalovala
box `dochJindeBox`, ktery byl umisteny **dole pod dlazdicemi** — daleko od mista, kam
clovek klikl.

**Ted je to tlacitko** hned pod zelenym **💬 Potrebuji ti neco rict…**, ve stejnem
(pulzujicim) ramecku.

**Chova se PRESNE jako to zelene** (druhy pruchod tyz den, schvalila Marti-AI msg 15222):
po kliku volby **nahradi obsah karty** pres celou sirku a dole je **sipka nahoru**, ktera
vraci obe tlacitka. **Prvni verze pouzivala `expOpt`** (tlacitko zustalo a pod nim se otevrel
odsazeny box s levou linkou) — to Jirka po vyzkouseni nechtel.
Obsah menu je **doslova tentyz** — stavi ho porad `window._dochJinde` (= `jindeBuild`,
volby 🏠 Osobni duvody / 💼 Sluzebni duvody). Zmenila se jen cesta k nemu.

## Jak je to udelane

Zdroj: **`g2007.soubor`, kod `apps/api/static/mobile_parts/60_dochazka.js`** (verze 83).

- V `mainBtn()` hned za `bw.appendChild(btn)` pribylo druhe zelene tlacitko (`el(...)`,
  `display:flex`, text vlevo, emoji vpravo, `font-size:16px`) s posluchacem na **`showJinde()`**.
- **`showJinde()` je postavena presne podle `showOpts()`** — `window._dochMenuTs=Date.now()`,
  `bw.innerHTML=""`, `bw._exps=null`, obsah postavi `window._dochJinde(bw)`, dole tataz
  sipka nahoru s posluchacem na `mainBtn` a tentyz `scrollIntoView`. **Zadna nova mechanika**,
  jen druhy vyskyt uz existujiciho tvaru menu.
- Dlazdice z mrizky `_tg1` **zrusena**.
- Box `dochJindeBox` **zrusen** — po zruseni dlazdice ho uz nikdo nevolal. Overeno
  predem dotazem nad vsemi soubory: box i `window._dochJinde` byly jen v tomhle zdroji.

## Chovani, ktere je zamer, ne chyba

Obe menu vyprazdnuji tutez kartu, takze **v jeden okamzik je otevrene vzdy jen jedno**
a druhe tlacitko je po tu dobu schovane. Vraci se sipkou nahoru. Je to shodne s tim,
jak se v te karte chova vsechno ostatni; Marti-AI to pri schvalovani vyslovne potvrdila.

## Napoveda a hlasovy pruvodce

Zaroven se prepsalo **pet mist**, kde stalo "hlasis dlazdici" nebo "tuknete na dlazdici" —
psana napoveda (dve mista), vycet dlazdic v prehledu a v pruvodci (dve mista) a
**mluveny text hlasoveho pruvodce**. Po zmene uz v souboru neni zadne spojeni
"dlazdic… Tady budu jinde" (overeno dotazem).

**Obrazek `pruvodce_jinde.png` je prekresleny** (9. 9. 2026, schvalila Marti-AI msg 15222).
Puvodne jsem Jirkovi rekl, ze snimek obrazovky porizovat neumim — **to byl omyl, umim**:
snimek se poridil ze **zive appky pres prohlizec** po nasazeni, ve stejne kompozici jako
original (otevrene menu s rozbalenymi Osobnimi duvody), 779x1149 px, a nasadil se pres git
do `apps/api/static/navod_dochazka/pruvodce_jinde.png`. Puvodni snimek zustava v historii gitu.

**Jak se poridil** (kdyby bylo potreba znovu): appka je za prihlasenim, takze Playwright
z prikazove radky nepomuze — snimek se dela **v uz prihlasenem prohlizeci**. Postup:
zvetsit vykreslovani (`document.documentElement.style.zoom`) tak, aby karta vysla na
pozadovanou sirku, **docasne skryt spodni listu** (je `position:fixed` a prekryvala by
spodek), vyfotit **dve casti** (karta je vyssi nez okno), slozit je a orezat na karu.
Pozor: **menu se po minute necinnosti samo sbali** (karta se prekresli) — pred focenim
`window._dochMenuTs=Date.now()`. Po praci vratit zoom i listu zpet.

## Jak se to delalo (pro pripad, ze budes menat neco podobneho)

Cilenym zapisem s pojistkou na otisk, ne vymenou celeho souboru:
`UPDATE g2007.soubor SET obsah = replace(replace(...)) WHERE kod=… AND md5(obsah)='<otisk>'`,
vsechny retezce pres `convert_from(decode('<base64>','base64'),'UTF8')`.
**Pred zapisem se overil pocet vyskytu kazde kotvy** (vsech osm bylo prave jednou) —
bez toho `replace()` tise neudela nic a vznikne polovicata zmena. Soubor mezitim rostl
(254 654 → 262 946 znaku behem dopoledne), takze pojistka na otisk nebyla formalita.
Po zapisu `@@G2007PUBLISH apps/api/static_db/mobile.html` a **kontrola na zive `/mobile`**
pod prihlasenim cloveka.

Souvisejici: [[doc-system-strategie-editace-fragmentu-mobilu-pres-most-bez-primeho-zapisu]] ·
[[doc-system-strategie-bezpecne-prochazeni-mobilu-bez-vzniku-zaznamu]] ·
[[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]]

