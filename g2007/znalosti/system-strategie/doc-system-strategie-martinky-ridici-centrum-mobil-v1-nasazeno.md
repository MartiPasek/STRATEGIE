# Ridici centrum v mobilni appce - NASAZENO+OVERENO ZIVE 3.8.2026 vecer (dlazdice v sekci Ukoly)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co je nasazeno (artefakt mobile.html v15, md5 441a0e9a8f8fcaa1c8aaec91e6b8e940)

Mobilni RIDICI CENTRUM dle smeru `smer-martinky-ui-ridici-centrum` — vstup od lidi (jako dochazka):

- **Dlazdice** 🌸 "Ridici centrum / Lide · AI tymy" v sekci UKOLY (fragment `20_home_phone_notifs.js`, hned vedle dlazdice Ukoly). Badge (ruzovy #db2777) ukazuje pocet veci cekajicich na prihlaseneho cloveka; pri 0 je skryty.
- **4 obrazovky** (fragment `75_martinky_centrum.js`, v3): `martinky` (lide + pritomnost z tenant.att_entry + pocet domen + kolik ceka), `martinky_clovek` (⚡ceka / 👩chat s Maminkou nahled / 🌸Martinky s pocty), `martinky_domena` (ukoly domeny), `martinky_ukol` (cele vlakno ukol_zprava + Schvalit/Vratit + chat s Martinkou pres martinka_chat).
- **Backend** `g2007.python martinka_centrum` v2 — pohledy lide|clovek|domena, prava vlastnik sve / rodic (is_marti_parent) vse, `__uid__` placeholder v args. POZOR v2 fix: `sum(count(*))` vraci NUMERIC → Decimal → 500 pri JSONResponse; nutny `::int` cast (stejna gotcha jako `::float8` u martinka_prehled).

## KRITICKA GOTCHA — fragmenty mobile.html: script bloky != fragmenty

Fragment NENI script blok. Hranice fragmentu jsou bajtove rezy zivaku — jeden `<script>(function(){...try{...}})()` blok se klidne sklada z NEKOLIKA fragmentu (fragment 73_zexec KONCI hlavickou ciziho bloku vc. `try {`, fragment 74 ZACINA az `function claude27()`). Dusledky pro kazdy novy fragment vkladany doprostred:

1. **Importy bloku plati pro cely blok** — koncovy blok importuje jen api/esc/el/go/topbar/home/back/... a NEMA SCREENS, app, render. Hola jmena = ReferenceError (tise spolknuty try/catch → obrazovka se prosto nezaregistruje).
2. **NIKDY nedeklarovat sdilena jmena** (`var render` apod.). Obsah bloku je uvnitr `try { }` = BLOK, a `function render(){}` z fragmentu 74 je v nem block-scoped lexikalni deklarace → `var render` v temze bloku = **SyntaxError "Identifier 'render' has already been declared" → umre CELY script blok pri parsovani** (vsechny obrazovky vsech fragmentu v bloku: cil, exec_approval, vpfinzak...). Presne tohle byla ziva regrese 3.8. vecer (artefakt v13/v14), opravena v15.
3. **Spravny vzor**: vsechno primo pres `window.__M2W.app` / `window.__M2W.render()` / `window.__M2W.SCREENS.xxx=fn` (over. vzor claude27 a registrace cil v 73_zexec). `window.__M2W.SCREENS` je publikovan drive (blok s 73_pref_poptavka) a uz se NEpreprirazuje — registrace do nej je bezpecna bez ohledu na poradi fragmentu.
4. Fragment 75 pri registraci **doregistrovava i `vpfinzak`** (Kristy B2) — jeji vlastni registrace `SCREENS.vpfinzak=` v 73_zvp je hole jmeno a tise pada; funkce je hoisted, tak ji 75 zvedne. Pri buducim zasahu do 73_zvp opravit primo tam.

## Overeno zive (prohlizec, 3.8.2026 ~22:00)

`window.__M2W.SCREENS` = 129 obrazovek vc. martinky/martinky_clovek/martinky_domena/martinky_ukol + vpfinzak + puvodni cil/cil_detail/cil_new/exec_approval (regrese zahojena). Proklik: dlazdice → lide (Eliska 5 domen/2 ceka, Marti 3 domeny/makam od 6:33) → Eliska → ukol #9 vlakno s kontraktem, tool-callem, vysledkem, tlacitky Schvalit/Vratit a chatem → domena kalkulace_obecna. Zadny SyntaxError v konzoli.

## Soubory
- g2007.soubor zdroj `apps/api/static/mobile_parts/75_martinky_centrum.js` (v3, md5 0f5d34749bbc140a2f7ac9d2e32852f0, 14999 zn)
- g2007.soubor zdroj `apps/api/static/mobile_parts/20_home_phone_notifs.js` (dlazdice + badge)
- artefakt `apps/api/static/mobile.html` v15 (931300 zn), slozeno_z 30 polozek (75 pred 74)
- g2007.python `martinka_centrum` v2 (md5 14b0c3eff7db451f0b24e9818b1db817)

