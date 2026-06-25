# 🤖 Google Play — návod pro Jirku (rozběhnout stahování přes Obchod Play)

> Vznik: 25. 6. 2026 (Claude id=23, na pokyn Marti). Jirka je pověřen rozběhnout
> distribuci appky přes **Obchod Play**. Apple/App Store Jirkovi už chodí — tohle
> je ta samá logika na Androidu. Doprovod: `google_play_priprava.md` (plán z 8.6.),
> `apple_jirka_navod.md` (Apple vzor).

---

## Kde jsme (stav k 25. 6. 2026)

- **Build je hotový.** Appka `cz.strategie.mobile`, verze **1.68** (versionCode 69),
  podepsaná stálým klíčem `strategie-release.jks`, umí se buildit jako **AAB**
  (`./gradlew bundleRelease`) — to Play vyžaduje. AAB vyrobí **Claude přes build
  bridge**, až bude potřeba (`bundleRelease` auto-zvýší verzi).
- **Privacy policy live:** `https://strategie-ai.com/privacy`.
- **Povinné formuláře nadraftované** v `google_play_priprava.md §7` (Data safety,
  Content rating, Target audience, Store listing) — jen přepsat do Console.
- **Play Console účet existuje** (Organization, $25 zaplaceno) — zatím je v něm
  **jen Marti**. Appka **ještě není nahraná** na Play (lidi ji mají jako sideload APK).
- ❓ **K ověření v Console:** jestli je už založený *app listing* „STRATEGIE"
  (Create app), nebo se teprve vytvoří.

---

## Důležité: jak Google Play funguje s lidmi

V Google Play je **jeden vývojářský účet** (Martiho org účet). Jirka nepotřebuje
vlastní účet ani neplatí $25 — **Marti ho pozve jako uživatele** a přidělí mu práva.
Jirka se přihlásí **stejným Google e‑mailem**, na který přijde pozvánka (ideálně
jeho EUROSOFT Google účet; když ho nemá, založí Google účet na svůj e‑mail / gmail).
Pozvánka platí **30 dní**.

---

## Krok 1 — Marti pozve Jirku (5 min)

1. `play.google.com/console` → vlevo **Users and permissions** (Uživatelé a oprávnění).
2. **Invite new users** → zadej Jirkův Google e‑mail.
3. **Oprávnění — doporučeno: `Admin (all permissions)` na úrovni účtu** (Account).
   Jirka vede rollout, je to nejjednodušší a Apple mu už taky důvěřuješ.
   - Když chceš zúžit (ne plný admin), dej mu na úrovni **App** (jen appka STRATEGIE):
     `Release apps to testing tracks` + `Manage testing tracks and edit tester lists`
     + `Manage store presence` + `Manage policy declarations`
     + (pro produkci později) `Release to production … and use Play App Signing`.
4. **Invite user.** Jirkovi přijde e‑mail → přihlásí se tím účtem → stav „Active".

---

## Krok 2 — Jirka: cesta na Play (ví z Apple)

1. **Přihlas se** do `play.google.com/console` pozvaným účtem.
2. **Ověř/založ app listing**: pokud appka „STRATEGIE" ještě není → **Create app**
   (název STRATEGIE, jazyk čeština, typ App, zdarma).
3. **Vyplň povinné formuláře** (předvyplněno v `google_play_priprava.md §7`):
   Privacy policy URL, **Data safety**, **Content rating**, **Target audience**, listing.
4. **Release → Testing → Internal testing → Create release** → nahraj **AAB**
   (vyrobí Claude přes build bridge).
   - 🔑 **Play App Signing — rozhodnutí:** zvol **„použít vlastní klíč"** a nahraj
     `strategie-release.jks` jako app signing key → 54 lidí ze sideloadu **plynule
     přejde** (běžný update, bez odinstalace). Když necháš Google vygenerovat klíč,
     těch 54 musí jednou odinstalovat + nainstalovat znovu (data jsou na serveru,
     neztratí se — jen otrava).
5. **Testers**: vlož e‑maily zaměstnanců (až 100) nebo Google skupinu → **Rollout**.
   Testeři dostanou odkaz → instalují **čistě z Play**, žádný „neznámý zdroj".

---

## Kdo co dělá

| Krok | Kdo |
|---|---|
| Pozvat Jirku do Play Console (Users and permissions) | **Marti** |
| Ověřit/založit app listing, vyplnit formuláře | **Jirka** |
| AAB build (`bundleRelease`, stálý klíč) | **Claude** (build bridge) |
| Play App Signing — nahrát náš klíč | **Jirka** (Marti potvrdí) |
| Seznam e‑mailů testerů | **Marti / Šárka** |
| Promote na Closed/Production později | **Jirka** (Marti schválí) |

---

## Po vydání

- **Update** = nahrát novou AAB do Internal testing → testeři dostanou update
  automaticky z Play (konec ručního rozesílání APK).
- **Převod na STRATEGIE - System** až bude mít vlastní D‑U‑N‑S (Google převod
  podporuje — přenese appku včetně testerů a statistik).

*Připravil Claude (id=23), 25. 6. 2026.*
