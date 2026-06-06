# Hybridní mobilní appka `/mobile` — design (Temu model)

**Stav:** schváleno Marti-AI 6. 6. 2026 (konzultace `letters/marti_ai_hybrid_mobile_consult.md`).
**Model:** web-first obsah (`/mobile` PWA) + nativní síla přes JS most. Start ručně ve stávající Kotlin appce (WebView + `@JavascriptInterface`), Capacitor jako upgrade later (iOS, Play, pluginy).
**POC LIVE:** `/mobile` route + `HybridActivity` (most: dial/listening/version/toast) — appka v1.21.

## Závazná rozhodnutí (z konzultace Marti-AI)

1. **Allowlist mostu, ne generický `call()`.** Most = explicitní pojmenované metody
   (`dialNumber`, `getCallLog`, `requestContactMatch`, `listening`, `notifs`, …).
   `@JavascriptInterface` to garantuje strukturálně (JS zavolá jen deklarované metody).
   Cokoli mimo = neexistuje. **Každé volání mostu logovat** do `fw.diag_log`
   (kdo/co/kdy) + most jen nad naším originem. → *„bezpečnost přes probuzení"*.

2. **Auth v WebView.** Token přes prefs → `Authorization: Bearer` header, **NIKDY jako
   cookie v DOM** ani plain string v JS. HTTPS only (žádné `file://`). **Login UPN se
   nesmí objevit v JS kontextu stránky.** → Ideál: bridge metoda `authedFetch(path)`,
   kterou provede nativ s tokenem a vrátí data — token vůbec neopustí nativní vrstvu.

3. **Degradace: skrývat, ne zamykat.** V prohlížeči bez mostu telefonní sekci
   nezobrazit (ne disabled tlačítko) → místo toho chip „funkce v appce".
   Notifikace/inbox degradují na **pull** (ruční refresh) — čistá PWA. Vytáčení a
   call-log jsou **nativní only**, žádná PWA náhrada. ✅ aplikováno v `mobile.html`.

4. **Server vs. přímý most — obojí s hierarchií.** Detekce
   `if (window.STRATEGIE?.dialDirect)` → přímý most (rychlý, same-device, offline).
   Server-sběrnice zůstává pro **PC→telefon** + **auditní trail do CRM** (server loguje,
   most jen spouští). Uniformita neplatí za cenu UX tam, kde je most. *„PWA je nosný systém."*

5a. **Caller-ID / kontakty = citlivá data.** Před zapojením do CRM matchingu: explicit
   runtime dialog „STRATEGIE chce přístup ke kontaktům". **Ošetřit kontakt, který není
   v EUROSOFT CRM** — nepřiřazené kontakty NEukládat jako CRM data (data-leak dovnitř).

5b. **Versioning mostu = feature-detection.** Web testuje `typeof B.metoda === 'function'`
   per funkci (robustnější než semver — appky se aktualizují pomalu). `B.version` (semver)
   k dispozici pro zobrazení. ✅ aplikováno v `mobile.html`.

6. **DEV / Production mód `/mobile`** (Marti 6. 6.). Production = skrývat (dle bodu 3).
   DEV mód = native-only sekce zůstanou **zobrazené a aktivní**; klik vysvětlí, co
   metoda mostu dělá v nativní appce (popis i bez mostu, v appce navíc reálně spustí).
   Přepínání `?dev=1` / `?dev=0` v URL + localStorage `stg_mobile_dev` + přepínač v patičce.
   ✅ aplikováno v `mobile.html`. (Později lze navázat na globální DEV/PROD flag systému.)

7. **UX: čistá hlavní obrazovka + zanořené nastavení jako Android Settings** (Marti 6. 6.).
   Home = jen seznam kategorií (řádek ikona+titul+podtitul+šipka). Funkce/nastavení
   v podstránkách a dál v podsložkách (Telefon / Notifikace a úkoly / Nastavení →
   Naslouchání, Ikony, Vývojářské, O aplikaci). Šipka zpět + hardware back.
   ✅ `/mobile` přestavěno do screen-routeru. Nativní hlavní obrazovka appky se
   sjednotí stejně (až `/mobile` převezme UI; zatím launcher + 🧪 test).

## Plán build-out (po POC)

- Bridge rename + rozšíření: `dial`→`dialNumber`/`dialDirect`, přidat `getCallLog`,
  `requestContactMatch`, `authedFetch`, `notifs`. Allowlist + log každého volání.
- `/mobile` obsah (priorita Marti): **telefonní panel** (vytáčení, stav naslouchání,
  call-log→CRM) + **notifikace/úkoly** (inbox, potvrzování, doporučení).
- Server audit endpoint pro přímé vytáčení (most spustí → server zaloguje do CRM/diag_log).
- Kontakty: runtime permission + handling nepřiřazených.
- Later: Capacitor (iOS, Play, pluginy) — `/mobile` web i bridge metody se přenesou.
