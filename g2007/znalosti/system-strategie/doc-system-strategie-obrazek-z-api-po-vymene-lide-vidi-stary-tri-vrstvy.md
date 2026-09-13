# Po vymene obrazku z API lide vidi stary: tri vrstvy, ktere to zpusobily (13. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Po vymene obrazku z API lide vidi stary - tri vrstvy pod sebou

Narazeno naostro 13. 9. 2026 pri vymene fotky persony (Jirka Honomichl / Claude-28). Plati pro **jakykoli obrazek vydavany z API**, nejen pro fotku persony.

Kazdou z techto tri vrstev jsme museli resit zvlast a **kazda sama o sobe stacila k tomu, aby clovek videl starou fotku.**

## 1) Server neposilal zadny pokyn k ukladani

Odpoved s obrazkem mela otisk (`ETag`) i datum, ale **zadnou hlavicku `Cache-Control`**. Prohlizec i telefon si ji proto smely nechat podle vlastni uvahy a novou si nevyzadaly.

**Oprava** (commit `9872d235`): k vydeji obrazku pridana hlavicka `Cache-Control: no-cache`. To **NEzakazuje ulozeni** - jen rika "pred pouzitim se vzdy zeptej serveru".

## 2) Pouzita odpoved na soubor sama nevyhodnoti podmineny dotaz

`FileResponse` otisk i datum **posila**, ale prichozi `If-None-Match` / `If-Modified-Since` **sama NEvyhodnoti**. Overeno naostro: oba dotazy vratily 200 a cely soubor, nikdy 304.

Dusledek: bez dalsi opravy by se obrazek po zavedeni `no-cache` stahoval **pri kazdem otevreni obrazovky**.

**Oprava** (commit `a7a0f26b`): otisk se pocita rucne (cas zmeny + velikost souboru), pri shode se vraci prazdne 304. **Otisk MUSI byt v uvozovkach** (RFC 7232) - bez nich ho nektere klienty (typicky iOS) neuznaji a 304 nikdy nenastane.

Overeno po nasazeni: prvni dotaz 200, druhy se stejnym otiskem **304 a nula bajtu**, dotaz s jinym otiskem zase 200, a po skutecne vymene obrazku se otisk zmenil a klient dostal novy obsah.

## 3) ⭐ iPhone drzi ulozenou kopii z doby PRED opravou - a restart appky ji nesmaze

**Tohle byla nakonec ta vrstva, kterou clovek videl.**

| | Android | iPhone |
|---|---|---|
| appka | ma **nativni most**, obrazek si stahne sama pri kazdem startu (`avatarDataUrl` v `HybridActivity.kt`, od v1.25) | **jen obal kolem webu** (`APP/iOS/mobile/ContentView.swift`, ~98 radku, zadny most) |
| odkud bere obrazek | z nativni cesty, vzdy cerstve | **webovou cestou** - a plati pro nej ulozena kopie ve WKWebView |

Ulozena kopie z doby pred opravou hlavicek **prezije i uplne ukonceni appky** (odsunuti z prehledu bezicich). Proto rada "zavri a znovu otevri appku" u iPhonu **nepomuze a pomoct nemuze**.

**Oprava** (dilek `apps/api/static/mobile_parts/10_core.js`, publikovano 13. 9. 2026): k adrese obrazku se pripojuje `?v=` + cas startu appky. Pri kazdem spusteni tak vznikne jina adresa, stara ulozena kopie se nepouzije; behem behu se adresa nemeni, takze se obrazek nestahuje dokola. Android to nijak neovlivni - tam nativni cesta adresu stejne prepise.

**Vyhoda teto cesty:** je to zmena **obsahu** aplikace, tedy **bez vydavani nove appky** do obchodu. U iPhonu je to casto jedina rychla cesta.

## Co si z toho vzit

- **"Nasadil jsem to a v prohlizeci to vidim" neznamena, ze to vidi lide v telefonu.** Android a iPhone se chovaji jinak a diagnoza pro jeden neplati pro druhy.
- **Nejdriv zjisti, na cem se clovek diva** (Android appka / iPhone appka / zastupce stranky / prohlizec). Bez toho se hleda chyba na spatnem miste - 13. 9. jsem pul hodiny cetl androidi kod, zatimco Jirka mel iPhone.
- U obrazku z API pocitej se **vsemi tremi vrstvami**, ne jen s prvni.

## Souvisi

- `doc-system-strategie-fotka-na-domovske-obrazovce-je-avatar-persony`
- `doc-system-strategie-avatar-persony-zaloha-v-databazi-a-samoobnova`

