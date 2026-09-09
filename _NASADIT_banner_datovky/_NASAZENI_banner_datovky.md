# Nasazení: výrazný banner u synchronizace datovek (mobile.html)

**Pro:** kdo nasazuje na strategie-ai.com (deploy)
**Od:** Peta — úpravu připravil asistent, přikládám hotový soubor.

## Co se mění (zadání)
V záložce **Datové schránky** (mobilní appka i web `/mobile`) se po kliknutí na
**Synchronizovat** zobrazovala jen malá hláška u horního okraje (`_shotToast`) —
snadno se přehlédla. Nově se ukáže **výrazný barevný banner uprostřed obrazovky**:

- modrá = „Synchronizuji datovku…" (probíhá)
- zelená = „Hotovo: X nových" (úspěch)
- červená = „Chyba: …" (chyba, nebo sync proběhl s chybou)

Pozadí se NEztmavuje (appka pod bannerem zůstává vidět), banner zmizí sám
(hotovo ~3,5 s, chyba ~5 s) nebo po kliknutí na něj.

## Změněný soubor
`apps/api/static/mobile.html` — jediný dotčený soubor.
Upravená verze je už uložená u Peta v repu na stejné cestě
(`C:\Projekty\Strategie\apps\api\static\mobile.html`) a je i v příloze chatu.

## Co konkrétně bylo upraveno (k rychlé kontrole)
1. Hned za `_shotToastHide()` (cca ř. 6137) přidány funkce
   `_isdsBanner(msg, kind)` a `_isdsBannerHide()`. Vykreslí vystředěný banner;
   `kind` ∈ {`progress`,`ok`,`err`}. Vrstva pozadí má `pointer-events:none`
   (neblokuje appku, neztmavuje).
2. Funkce `isdsSync(id, days)` (cca ř. 7600) přepsána z `_shotToast(...)`
   na `_isdsBanner(..., 'progress'|'ok'|'err')`. Když přijde
   `r.errors`, použije se `kind='err'`.
3. Žádné jiné toasty (screenshoty apod.) se neměnily.
   Kontrola syntaxe inline JS (`node --check`) prošla OK.

## Nasazení — 2 kroky
**1) V repu commit + push (na počítači, kde je repo):**
```
cd C:\Projekty\Strategie
git add apps/api/static/mobile.html
git commit -m "mobile: vyrazny banner u synchronizace datovek"
git push origin main
```

**2) Na cloud APP serveru (kde běží služba STRATEGIE-API):**
```
cd C:\Projekty\STRATEGIE
.\scripts\deploy_current.ps1
```
(skript udělá `git pull origin main` + restart služby + health-check)

Po nasazení v appce/prohlížeči **tvrdé obnovení (Ctrl+F5)**, ať se nenačte
stará verze z cache. Hotovo se pozná na záložce Datové schránky → Synchronizovat.
