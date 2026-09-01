# Dve pasti pri uprave obsahu mobilu - publikace vypusti i cizi rozdelanou praci, a api() bere jako prvni parametr METODU

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Dve pasti pri uprave obsahu mobilni aplikace

Naslo se 1. 9. 2026 (Claude-28 / Jirka) pri napojovani karty "Moje hodiny".
Doplnuje postup v [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]].

## 1. `@@G2007PUBLISH` vypusti do provozu I CIZI rozdelanou praci

**Publikace neslozi jen tvuj dilek - slozi stranku ze VSECH dilku v jejich aktualnim stavu.**
Kdyz nekdo jiny mezitim upravil svuj dilek a jeste nepublikoval, **tvoje publikace posle
do provozu i jeho zmenu**, aniz by o tom kdokoli vedel.

Realny pripad 1. 9. 2026 - Claude-28 publikoval kvuli `60_dochazka.js` a spolu s tim se
naostro dostala i uprava `50_skupiny_vyroba.js`, kterou tehoz dne v 11.27 udelal Claude-26
(Peta) a nechal nepublikovanou. Poznalo se to az podle toho, ze slozena stranka narostla
o 1 494 znaku vic, nez byla vlastni zmena.

**Co s tim:**
- **Pred publikaci se podivej, co jeste ceka**, dotazem na dilky zmenene od posledni publikace:
  porovnej `updated_at` dilku (`kod LIKE 'apps/api/static/mobile_parts/%'`) proti `updated_at`
  artefaktu `apps/api/static_db/mobile.html`.
- **Kdyz tam neco ciziho je, ozvi se autorovi driv, nez publikujes.** Muze mit rozdelano.
- **Po publikaci porovnej narust delky** slozene stranky s velikosti vlastni zmeny.
  Kdyz nesedi, publikoval jsi jeste neco jineho - dohledej co a rekni to autorovi.
- Neni to duvod nepublikovat - je to duvod **vedet, co poustis**, a rict to.

## 2. `api()` v mobilu bere jako PRVNI parametr metodu, ne adresu

Pomocna funkce v mobilu ma tvar **`api(method, path, body)`** a `path` musi byt **plna adresa
vcetne predpony `/api/v1/erp`**. V prohlizeci se vola `fetch(path, ...)` bez jakekoli predpony,
v appce jde pres nativni most `authedFetch(method, path, body)`.

```
SPATNE   api("/app/dochazka/moje-mesic?rok=2026")
SPRAVNE  api("GET","/api/v1/erp/app/dochazka/moje-mesic?rok=2026")
```

**Past je v tom, ze se to NEPOZNA jako chyba** - funkce vrati `null` (ma v sobe
`.catch(function(){return null;})`), takze obrazovka jen tise napise, ze se data nepodarilo
nacist. V konzoli neni nic. Vypada to jako vypadek serveru, pritom je to prekleplá adresa.

**Overuj tim, ze si vzor opises z existujiciho volani v tomtez dilku**, ne z pameti -
vsech ~30 volani v `60_dochazka.js` ma tvar `api("GET","/api/v1/erp/app/...")`.
Funkce vraci Promise s uz rozparsovanym JSONem (ne Response), takze `.then(function(j){...})`,
zadne `.json()`.

## 3. Mensi poznamka - zive `/mobile` je delsi nez artefakt v databazi

Stazena stranka `/mobile` byla 1. 9. 2026 o **1 315 znaku delsi** nez obsah artefaktu
`apps/api/static_db/mobile.html` v databazi. Neni to konci radku (v odpovedi nejsou zadne CR)
a zacatek i konec stranky sedi. **Cim to je, zjisteno nebylo** - vypada to na neco, co server
pridava az pri odeslani. Uvedeno proto, aby priste nikdo nehlasil falesny poplach - **porovnavat
delku zive stranky s delkou v databazi nema smysl**, porovnavej obsah konkretniho bloku.

