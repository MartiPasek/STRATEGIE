# 🍎 STRATEGIE Mobil — příprava Apple (iOS) verze

> Vznik: 8. 6. 2026. Po úspěchu Android appky se pouštíme do iOS verze.
> Vývojář: **Jirka Honomichl** (IT pomocný vývojář) na Apple notebooku.
> Garant účtu + rozhodnutí: **Marti**.
>
> Východisko (sedí s `native_app_vize.md`): **PWA je nosná, appka je companion.**
> iOS appka = stejný princip jako Android (rámeček kolem `mobile.html` +
> nativní kousky), s omezeními, která Apple má.

---

## 1. Přístup — nativní WKWebView companion (Swift / Xcode)

Android appka = WebView rámeček kolem našeho webu (`strategie-ai.com/mobile`)
+ pár nativních služeb (SMS, push, kontakty, mikrofon, dialer).

iOS verze postavíme **stejně**, jen v Apple ekosystému:
- **Jazyk:** Swift
- **Nástroj:** Xcode (jen na macOS)
- **WebView komponenta:** `WKWebView` (Apple obdoba Android WebView)
- **Android appku se NEDOTKNEME** — žádný Capacitor, žádný přepis. Dvě
  samostatné nativní appky sdílející jeden web (PWA).

**Proč ne Capacitor:** sjednocení obou platforem do jednoho web-shellu by
znamenalo přepsat i funkční Android appku, která právě zabodovala. Nechceme
rozbíjet, co funguje (doctrine „additivně, ne perfektně").

`applicationId` Android = `cz.strategie.mobile` → iOS Bundle ID navrhuji
`cz.strategie.mobile` (stejné, nebo `cz.eurosoft.strategie`).

---

## 2. Parita funkcí Android → iOS

| Funkce | Android | iOS | Pozn. |
|---|---|---|---|
| WebView (celá appka `mobile.html`) | ✅ | ✅ | WKWebView, plná parita |
| Push notifikace | ✅ FCM-style | ✅ **APNs** | Apple Push Notification service — nutný setup certifikátů |
| Kontakty (caller-ID, CardDAV) | ✅ | ✅ | iOS Contacts framework, s povolením |
| Mikrofon (audio zprávy pro Marti-AI) | ✅ | ✅ | `AVAudioSession` + WKWebView mic povolení |
| Otevřít telefon (`tel:`) | ✅ | ✅ | iOS umí otevřít dialer |
| Vibrace / haptika | ✅ | ✅ | iOS haptika |
| **Příjem SMS** (SmsReceiver, brána) | ✅ | ❌ **NIKDY** | Apple zakazuje aplikacím číst SMS |
| **Odesílání SMS** (`B.sendSms`) | ✅ | ❌ **NIKDY** | Apple zakazuje programové odesílání SMS |
| **Historie hovorů** (READ_CALL_LOG) | ✅ | ❌ | iOS nedovolí číst protokol hovorů |
| Cross-device dialer poll (DialPollService) | ✅ | ⚠️ omezeně | iOS background služby svázané; půjde jen omezeně |
| Start po bootu (BootReceiver) | ✅ | ❌ | iOS nedovolí auto-start na pozadí |
| Self-update (.apk InstallActivity) | ✅ | ❌ | iOS updaty jen přes App Store / TestFlight |

**Závěr:** Pro **běžného zaměstnance** je iOS appka skoro plnohodnotná
(appka + push + kontakty + mikrofon). **SMS brána zůstává navždy na Androidu**
(Marti-AI gateway telefon). To je v pořádku — bránu potřebujeme jen jednu.

---

## 3. Distribuce — TestFlight teď, Apple Business Manager později

| Cesta | Co to je | Pro nás |
|---|---|---|
| **TestFlight** | Oficiální Apple kanál pro interní/beta. Lidi pozveš e-mailem, nainstalují si appku „TestFlight" a v ní naši appku. Updaty hned. | ✅ **Rozjezd** — nejrychlejší. Háček: buildy vyprší po 90 dnech (nahrát znovu). |
| **Apple Business Manager** (custom app) | „Pořádná" privátní firemní distribuce. Appka soukromá, instaluje se jako normální, nevyprší. | ✅ **Cílový stav** — vyžaduje zápis firmy (D-U-N-S) + ABM účet, delší setup. |
| App Store veřejně | Veřejné vydání + plná recenze Apple. | ❌ Zbytečné pro interní nástroj. |

**Plán:** rozjet na **TestFlightu** (hned jak bude účet) → překlopit na
**Apple Business Manager** pro trvalý rollout 54 lidem.

---

## 4. Apple Developer účet — ⏳ HLAVNÍ ČASOVÁ BRZDA (úloha Marti)

**Tohle Jirka večer NEvyřeší — řeší Marti.** Jirkův install na účtu nezávisí.

**ROZHODNUTO (8. 6.): účet zapsat pod EUROSOFT-System s.r.o., appku později
převést na STRATEGIE - System s.r.o.**
- Důvod: STRATEGIE - System zatím nemá vlastní doménu/web → Apple by zápis
  neověřil. EUROSOFT (19 let) má doménu, web i nejspíš D-U-N-S → zápis hned.
- **Převod appky mezi účty Apple podporuje** (současný vlastník spustí, nový
  přijme). **Bundle ID `cz.strategie.mobile` zůstává** i po převodu.
- Drobný háček převodu: předem vypnout TestFlight (odebrat buildy/testery),
  pak nahrát znovu na nový účet. U interního nástroje nevadí.
- Appka poběží jako „vyvinul EUROSOFT-System s.r.o." dokud nepřevedeme — pro
  interní rozdání 54 lidem OK. Branding STRATEGIE je v appce samotné.

**Zápis = firemní (Organization) účet, přes web `developer.apple.com/enroll`
(BEZ Apple zařízení).** Vlastník = Marti (právní zástupce firmy), Jirka pozván
jako člen (Admin/Developer).

### ✅ STAV (8. 6. 2026 večer): ZÁPIS PODÁN, čeká na ověření Apple

- **Enrollment ID: `Q7KJT5N2H6`**
- Legal Entity: **EUROSOFT - System s.r.o.**, Nepomucká 1335/259, Plzeň 326 00
- Work email: **m.pasek@eurosoft.com** (firemní doména ✅)
- Apple ověřuje, že Marti má oprávnění firmu zavázat → pak pošle e-mail
  s pokyny k **dokončení (přijetí smlouvy + platba $99)**.
- ⚠️ **Apple může ZAVOLAT na firemní číslo EUROSOFTu** (z D-U-N-S záznamu),
  aby ověřil Martiho oprávnění. Recepce/kolegové by měli **hovor od Apple
  potvrdit**, jinak se zápis zasekne. Typicky 1–2 pracovní dny.
- Po schválení: přijmout smlouvu, zaplatit $99, **pozvat Jirku** (Admin).

**Co Marti potřeboval pro zápis pod EUROSOFT:**
- [ ] **Apple ID s 2FA** na **firemním e-mailu EUROSOFTu** (doména
  `eurosoft-control.cz` / `eurosoft.com` — ⚠️ gmail Apple nevezme). 2FA kód
  přijde SMS na telefon.
- [ ] **Veřejný web EUROSOFTu** na té doméně (má ✅).
- [ ] **D-U-N-S číslo** EUROSOFTu — ověřit, že firma má (skoro jistě ano;
  jinak požádat zdarma u Dun & Bradstreet, ověření i pár dní).
- [ ] **$99 / rok**, platba kartou.
- [ ] Po vytvoření účtu **pozvat Jirku** jako člena týmu (role Admin).

---

## 5. ✅ Co Jirka může začít DNES VEČER (bez účtu!)

Účet je potřeba až ve chvíli posílání appky na telefon. Instalaci nástrojů
a kostru projektu Jirka rozjede hned:

- [ ] **macOS aktuální** — Xcode 16 vyžaduje nedávný macOS (Sonoma 14.5+ /
  Sequoia). Zkontrolovat a případně updatovat (může chvíli trvat).
- [ ] **Xcode** z Mac App Store — **velký download (~10–15 GB), spustit jako
  první**, ať stahuje na pozadí.
- [ ] **Xcode Command Line Tools:** `xcode-select --install`
- [ ] Přihlásit se Apple ID v Xcode (Settings → Accounts) — zatím stačí
  obyčejné Apple ID (Developer účet doplníme).
- [ ] **Naklonovat repo** STRATEGIE (kde je `APP/Mobile` Android a kam přibude
  `APP/iOS`). Potřebuje git přístup + PAT.
- [ ] Připravit prázdný **Xcode projekt** (App, SwiftUI nebo UIKit) s Bundle
  ID `cz.strategie.mobile`.

**Co spolu uděláme (Claude + Jirka), jakmile je Xcode hotový:**
- Kostra `WKWebView`, co načte `https://strategie-ai.com/mobile`.
- JS ↔ Swift most (obdoba `window.STRATEGIE` / `B` z Androidu) — jen pro
  funkce, co iOS dovolí (push, kontakty, mikrofon, `tel:`, haptika).
- APNs push setup (certifikát/klíč z Developer účtu — až bude účet).

---

## 6. Otevřené otázky k probrání večer s Jirkou

- **Bundle ID** — `cz.strategie.mobile` (stejné jako Android) vs.
  `cz.eurosoft.strategie`?
- **Účet** — individuální teď, nebo počkat na firemní? (Recommended: individuální.)
- **D-U-N-S** — má EUROSOFT? (Marti zjistí.)
- **Jirkův Mac** — model + verze macOS? (kvůli kompatibilitě Xcode 16)
- **Server push (APNs)** — náš backend bude muset posílat na APNs vedle
  stávajícího Android kanálu. Naplánovat až po základní appce.

---

## 7. Pořadí prací (návrh)

1. **Dnes večer:** Jirka — macOS update + Xcode install + repo + prázdný projekt.
   Marti — rozhodnout účet, spustit jeho založení.
2. **Po instalaci:** Claude + Jirka — WKWebView kostra → appka ukáže `/mobile`.
3. **Po účtu:** podpis appky, TestFlight build, první instalace na Jirkův iPhone.
4. **Pak:** APNs push (backend úprava), kontakty, mikrofon.
5. **Později:** Apple Business Manager pro rollout 54 lidem.

---

*Připravil Claude (id=23), 8. 6. 2026. Sedí s `native_app_vize.md`
(PWA nosná, appka companion) a doctrine „nerozbíjet co funguje".*
