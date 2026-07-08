# 📦 Sklad — mobilní čtečky (Zebra TC27) + skenovací tok ve STRATEGII

> **Status:** PARKOVÁNO — hardware předán k objednání (8. 7. 2026), softwarovou část řešíme později.
> **Zadavatel:** Marti. **Autor poznámky:** Claude ID23.

## 1. K čemu to je (use case)
Mobilní terminály na **sklad** pro:
- **Objednávání VKM** (materiál/položky do kalkulace/výroby),
- **Příjemky** (příjem zboží na sklad),
- **Výdejky na zakázky** (výdej materiálu na konkrétní zakázku).

Charakter použití: **občasné**, ne celodenní. Proto **mobilní tvar (telefon se čtečkou), NE pistole.**

## 2. Hardware — rozhodnutí
**Zebra TC27** — odolný „mobil se čtečkou".
- Objednávaný kus (Mironet): **WCMTBT27B6ABC2A6** — SE4710 2D imager, 6", BT + Wi‑Fi + **5G**, **6 GB / 64 GB**, 3800 mAh (vyměnitelná baterie), **GMS Android**.
- **Proč TC27:** telefonní tvar, integrovaný 2D skener, odolné (IP68, pády), Android 14 + Zebra LifeGuard (dlouhá podpora).
- **SE4710** = standardní dosah 1D/2D (čtení štítků z ruky na blízko/středně) — pro tenhle případ ideální. (Dálkové čtení regálů by chtělo SE4770/SE55 — nepotřebujeme.)
- **GMS = klíčové** — má Google Chrome + Play → naše PWA běží v Chromu, DataWedge funguje. Ne‑GMS/AOSP verzi NEbrat.
- Tip: pořídit **1 náhradní baterii** navíc = klid i bez celodenní výdrže.
- K ověření u prodejce: aktuální **Android 14 + LifeGuard**, přítomnost **DataWedge** (u Zebra Mobility DNA vestavěný zdarma).

### Staré terminály (Android 4.3, Symbol/Zebra) — NEPOUŽÍVAT
- Let's Encrypt certifikát (strategie‑ai.com) **není důvěryhodný na Androidu < 7.1.1** (od úno 2024, po vypršení křížového podpisu DST Root X3) → zařízení se k appce přes HTTPS ani nepřipojí.
- WebView Androidu 4.3 = pravěký, neumí moderní JS (naše PWA na něm neběží).
- Žádné bezpečnostní záplaty ani MDM/EMM. Obcházení (ruční import ISRG Root X1 / Firefox s vlastní CA) je křehké — nevyplatí se.

## 3. Architektura software (jak to napojíme — bez nativní appky)
- **Zebra DataWedge** posílá naskenovaný kód do aplikace jako **klávesnici** (Keystroke output) nebo jako **key events** (od DataWedge 7.3) → sken „napíše" kód rovnou do políčka ve **webovém formuláři naší PWA** v Chromu. **Zero‑code**, žádná nativní appka.
- Skladové obrazovky postavíme jako **webové stránky ve STRATEGII** (stejný princip jako docházka / `/moje-dochazka`), běží přes HTTPS na moderním Androidu.
- Nastavení na zařízení: DataWedge **profil** (output = Keystroke) + asociace na appku/aktivitu (Chrome/PWA) → sken padá do editovatelného pole.

## 4. Co postavit později (TODO, až přijde hardware)
- [ ] Skladové obrazovky ve STRATEGII: **Příjemka**, **Výdejka na zakázku**, **Objednání VKM** — s polem pro sken + potvrzení množství.
- [ ] Napojení na skladová data / zakázky (ujasnit: náš sklad vs Centrála DB_EC skladové tabulky; co přesně je „VKM" v jejich modelu — materiál/kalkulace).
- [ ] Tok skenování (naskenuj položku → dohledej → množství → potvrď → zápis dokladu).
- [ ] DataWedge profil (dokumentovat nastavení pro IT: output=Keystroke, associated app).
- [ ] Ověřit chování skeneru v PWA (fokus pole vs listener na key events) na reálném kusu.

## 5. Odkazy
- Zebra TC22/TC27 produkt: https://www.zebra.com/us/en/products/mobile-computers/handheld/tc2x-series/tc22.html
- Datasheet TC22/TC27: https://www.zebra.com/us/en/products/spec-sheets/mobile-computers/handheld/tc22-tc27.html
- DataWedge Keystroke output: https://techdocs.zebra.com/datawedge/8-1/guide/output/keystroke/
- DataWedge key events (web/PWA): https://developer.zebra.com/blog/listening-keypress-events-datawedge

— Claude (ID23), 8. 7. 2026
