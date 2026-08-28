# Dilky mobilu NEJSOU jedna spolecna closure - funkce sdilena mezi dilky se musi zaregistrovat do window.__M2W (27. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Nalez (overeno naostro v prohlizeci 27. 8. 2026)

Znalost `doc-system-strategie-editace-fragmentu-mobilu-pres-most-bez-primeho-zapisu`
v sekci "Souvisejici" tvrdi:

> "Fragmenty **nejsou samostatne IIFE** - jsou to hole deklarace funkci uvnitr JEDNE
> obalove funkce otevrene v `10_core.js` a zavrene az v `74_claude27_render_init.js`,
> sdileji `app`, `el`, `topbar`, `go`, `api` pres closure."

**Tohle uz neplati.** Skutecnost k 27. 8. 2026: kazdy dilek je **vlastni `<script>` blok
s vlastni IIFE**, ktera si zavislosti bere z `window.__M2W`. Konec dilku 48 vypada takto:

```
  } catch(e) { console.error('[mobile2] chyba ve fragmentu 48_hr_podminky_me.js:', e); }
  window.__M2W.hr_podminky.__setImpl(hr_podminky); window.__M2W.hr_me.__setImpl(hr_me); ...
})();
</script>
<script>
(function(){
  var _railSync=window.__M2W._railSync, api=window.__M2W.api, el=window.__M2W.el, ...
  try {
```

## Co z toho plyne

**Funkce deklarovana v jednom dilku NENI videt z jineho.** Kdyz na ni sahnes jmenem,
appka spadne na `ReferenceError: <jmeno> is not defined` - a spadne az **za behu pri
otevreni te obrazovky**, takze `node --check` pri publikaci projde a chyba se ukaze
teprve cloveku v telefonu.

**Postup pri sdileni funkce mezi dilky:**
1. V dilku, kde funkce zije, ji za `catch` blokem zaregistruj:
   `window.__M2W._mojeFunkce = _mojeFunkce;`
   (registrace **musi byt az za `} catch(e){...}`**, ne uvnitr - tam by ji shodila vyjimka).
2. V druhem dilku ji volej **plnym jmenem** `window.__M2W._mojeFunkce(...)`, ne holym.
   Radek s importy na zacatku IIFE se cte pri startu bloku, takze pridavat ji tam neni nutne.
3. Poradi dilku rozhoduje: registrace musi probehnout **driv**, nez ji druhy dilek zavola.
   Cislovani nazvu (48 pred 60) to zaridi.

## Jak se to projevilo

27. 8. 2026 pri prestavbe obrazovky "Muj prehled" podle nakresu Sarky Novotne byly
fotka a Novinky presunuty z dilku 48 do dilku 60 jako sdilene funkce. Publikace prosla,
`node --check` prosel, ale **obrazovka "Muj prehled" hazela `_mojeHlavicka is not defined`**
a byla na chvili nepouzitelna. Odhalilo to az proklikani v prohlizeci pres Playwright
(`page.evaluate(() => window.__M2W.muj_prehled())`).

**Ponauceni:** po kazde zmene, ktera saha na vic dilku naraz, obrazovku **otevri v prohlizeci**.
Publikace ani kontrola syntaxe tuhle tridu chyb nechyti.

## Bonus: jak testovat obrazovku mobilu bez telefonu

Playwright + ulozene prihlaseni + **`serviceWorkers: 'block'`** (bez toho jdou dotazy
mimo odchyt a data se nepodstrci) + `page.route()` na endpointy. Pak
`page.evaluate(() => window.__M2W.<obrazovka>())` a snimek. Overeno 27. 8. 2026.

