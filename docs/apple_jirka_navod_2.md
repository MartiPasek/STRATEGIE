# 🍎 Návod pro Jirku #2 — na reálný iPhone + mikrofon + TestFlight

> Ahoj Jirko! Kostra běží v simulátoru 🎉 a Apple účet je **schválený a zaplacený**.
> Teď: (A) lepší kostra (mikrofon + volání), (B) **appka na tvém iPhonu**,
> (C) uložit do našeho repa, (D) první **TestFlight**. Děláme to **odshora dolů**,
> po každé části je ✅ KONTROLA. Když se zasekneš, vyfoť a napiš Martimu.

---

## ČÁST A — Vylepšit kostru (mikrofon, volání, potáhni-obnov)

Tahle verze přidá to, co bez ní v iOS WebView nefunguje: **mikrofon** (diktování,
hlasové zprávy pro Marti-AI), otevření **telefonu** přes `tel:` a **pull-to-refresh**.

**A1. Přepiš `ContentView.swift`**
- V levém panelu Xcode klikni na **`ContentView.swift`**.
- **Smaž vše** a vlož obsah souboru z našeho repa: **`APP/iOS/ContentView.swift`**
  (Marti/Claude ti ho pošle, nebo ho najdeš v repu — viz ČÁST C).

**A2. Přidej oprávnění do Info.plist** (jinak iOS mikrofon nepustí)
- V levém panelu klikni na **projekt** (úplně nahoře, modrá ikona) → vyber **target `mobile`**
  → záložka **Info**.
- U **„Custom iOS Target Properties"** najeď myší na libovolný řádek → klikni **„+"**
  a přidej tyhle tři klíče (Key → Value):

| Key | Value (text uvidí uživatel při dotazu) |
|---|---|
| `Privacy - Microphone Usage Description` | `Aplikace používá mikrofon pro hlasové zprávy a diktování ve STRATEGII.` |
| `Privacy - Camera Usage Description` | `Aplikace může použít fotoaparát pro přílohy ve STRATEGII.` |
| `Privacy - Contacts Usage Description` | `Aplikace používá kontakty pro identifikaci volajících (caller-ID).` |

> (Stačí psát „Microphone" do políčka Key a Xcode ti nabídne celý název.)

> ### ✅ KONTROLA A
> Spusť **▶ (Cmd + R)** v simulátoru. Appka naběhne jako dřív. (Mikrofon vyzkoušíš
> až na reálném telefonu v části B — v simulátoru mikrofon není.)

---

## ČÁST B — Spustit appku na TVÉM iPhonu 🎉

**B1. Připoj iPhone k Macu** kabelem. Na iPhonu odsouhlas **„Důvěřovat tomuto počítači"**.

**B2. Zapni svůj iPhone jako vývojářský**
- Na iPhonu: **Nastavení → Soukromí a zabezpečení → úplně dole „Režim pro vývojáře"
  (Developer Mode) → zapnout** → iPhone se restartuje a potvrdíš.

**B3. Nastav podpis (signing) firemním týmem**
- V Xcode klikni na **projekt** (nahoře) → target **`mobile`** → záložka
  **„Signing & Capabilities"**.
- Zaškrtni **„Automatically manage signing"**.
- U **„Team"** vyber **EUROSOFT - System s.r.o.** (objeví se, protože účet je schválený
  a jsi pozvaný jako člen — když ho nevidíš, v **Xcode → Settings → Accounts** přidej
  firemní Apple ID a dej **Download Manual Profiles**, pak se Team objeví).
- **Bundle Identifier** nech `cz.strategie.mobile`.
- Xcode si sám vyrobí podpisový profil (chvíli to může „přemýšlet").

**B4. Vyber svůj iPhone a spusť**
- Nahoře uprostřed Xcode (výběr zařízení) vyber **svůj iPhone** (ne simulátor).
- Klikni **▶ (Run)**.
- Poprvé iPhone řekne, že vývojář není ověřený → na iPhonu:
  **Nastavení → Obecné → VPN a správa zařízení → u „EUROSOFT - System s.r.o." dej
  Důvěřovat** → zkus **▶** znovu.

> ### ✅ KONTROLA B
> Na **tvém iPhonu** běží **STRATEGIE Mobil** s logem v hlavičce a docházkou.
> Otevři „Tvoje Marti" / hlasovou zprávu → **mikrofon si řekne o povolení a funguje**.
> Klik na telefonní číslo → otevře se **dialer**. 🎉

---

## ČÁST C — Uložit iOS projekt do našeho repa (s Claudem)

> Ať je iOS projekt v gitu vedle Android appky (`APP/Mobile`). **Tohle dělej s Claudem**,
> ať se nerozhodí struktura.

- Cílová složka v repu: **`APP/iOS/`** (už tam je vzorový `ContentView.swift`).
- Marti ti pošle **URL repa + token (PAT)**.
- S Claudem: zkopíruješ svůj Xcode projekt (složku `mobile`) do `APP/iOS/`,
  `git add` → commit → push. Claude ti dá přesné příkazy.

---

## ČÁST D — První TestFlight (rozdat appku k testu)

> TestFlight = oficiální Apple kanál pro beta. Lidi dostanou pozvánku e-mailem,
> nainstalují appku „TestFlight" a v ní naši appku. Tohle uděláme spolu.

**D1. Archive** (build na odeslání)
- Nahoře vyber zařízení **„Any iOS Device (arm64)"** (ne simulátor).
- Menu **Product → Archive**. Po chvíli se otevře **Organizer** s buildem.

**D2. Nahraj na App Store Connect**
- V Organizeru klikni **Distribute App → App Store Connect → Upload** → projdi
  průvodcem (automatic signing). Nahrání chvíli trvá.

**D3. V App Store Connect**
- [appstoreconnect.apple.com](https://appstoreconnect.apple.com) → **My Apps**.
- Pokud appka ještě není založená: **+ → New App** (Platform iOS, název „STRATEGIE Mobil",
  Bundle ID `cz.strategie.mobile`, SKU klidně `strategie-mobile`).
- Záložka **TestFlight** → build se objeví (stav „Processing", pár minut).
- Přidej **interní testery** (e-maily kolegů s Apple ID) → dostanou pozvánku.

> ### ✅ KONTROLA D
> V appce **TestFlight** na iPhonu vidíš „STRATEGIE Mobil" a jde nainstalovat.

---

## ❗ Co iOS NEumí (a je to OK — řeší Android brána)
- **SMS** (příjem ani odesílání) — Apple zakazuje. SMS brána zůstává na Marti-AI Android telefonu.
- **Historie hovorů**, auto-start po bootu — Apple nedovolí.
- Self-update — updaty jen přes TestFlight / App Store.

## ➡️ Co spolu uděláme pak (Claude + Jirka)
- **Most web↔Swift** (`window.STRATEGIE` pro iOS) — kontakty (caller-ID), deviceId, haptika.
- **APNs push** — backend bude posílat na Apple vedle Androidu (úprava na naší straně).

Držím palce, Jirko! 🤝 Klid, krok po kroku.

---
*Připravil Claude (id=23), 10. 6. 2026. Navazuje na `apple_jirka_navod.md` + `apple_app_priprava.md`.
Kód: `APP/iOS/ContentView.swift`.*
