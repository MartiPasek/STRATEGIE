# 🤖 STRATEGIE Mobil — vydání na Google Play (Android)

> Vznik: 8. 6. 2026. Důvod: sideload („neznámé zdroje") straší zaměstnance
> a vypadá nedůvěryhodně. Google Play = čistá, důvěryhodná instalace.
>
> **Cena: $25 jednorázově** (navždy). Účet: **Organization pod EUROSOFT-System
> s.r.o.** (D-U-N-S už ověřený z Apple). Appku **později převedeme na
> STRATEGIE - System** (Google převod podporuje, přenese vše).

---

## 1. Dobrá zpráva: build je připravený

- Podpisový klíč **`strategie-release.jks`** (alias `strategie`) **už existuje**
  a podepisuje všechny verze (teď v1.61 / code 62). `keystore.properties`
  je na build stroji (gitignored).
- Pro Play stačí build ve formátu **AAB** (Android App Bundle):
  `./gradlew bundleRelease` → podepsaný `app-release.aab`. Signing config
  se aplikuje i na bundle. **Claude to zařídí přes build bridge.**

### ⚠️ Klíčové rozhodnutí — podpisový klíč na Play

54 lidí už má sideload appku podepsanou `strategie-release.jks`.
- **DOPORUČENO:** při prvním nahrání na Play zvolit **„použít vlastní
  podpisový klíč"** = nahrát `strategie-release.jks` jako **app signing key**.
  → Play verze má stejný podpis → zaměstnanci **plynule přejdou** ze sideloadu
  (běžný update, bez odinstalace).
- Alternativa (Google vygeneruje vlastní klíč): jednodušší, ale 54 lidí musí
  jednou **odinstalovat + nainstalovat znovu** (data jsou na serveru, takže
  se nic neztratí — jen otrava).

---

## 2. Účet — kroky pro Marti (Google Play Console)

1. Jdi na **play.google.com/console** → **Sign in** firemním Google účtem
   EUROSOFTu (ideálně na doméně EUROSOFTu, ne osobní gmail).
2. Vyber typ účtu **Organization / Business** (ne Personal).
3. Zaplať **jednorázový registrační poplatek $25**.
4. **Verifikace organizace:** Google chce
   - **D-U-N-S číslo** EUROSOFTu (stejné jako u Apple),
   - **ověřený firemní telefon a e-mail** (zobrazí se na profilu vývojáře),
   - název + adresu firmy (musí sedět na D-U-N-S).
5. Google org ověří (může pár dní, podobně jako Apple).
6. Po schválení **přidáš Claudovi/Jirkovi přístup** (Users & permissions).

> ⚠️ Stejně jako u Apple: bez D-U-N-S to nejde. EUROSOFT ho má → OK.
> STRATEGIE - System zatím D-U-N-S nemá → proto teď EUROSOFT, převod později.

---

## 3. První vydání — Internal testing (privátní, hned)

Po schválení účtu (dělá Claude + Jirka, Marti jen schvaluje):

1. **Create app** → název „STRATEGIE", jazyk čeština, typ App, zdarma.
2. Vyplnit povinné appkové formuláře (i pro testing track):
   - **Privacy policy URL** → bude na `https://strategie-ai.com/privacy`
     (Claude připraví stránku).
   - **Data safety** formulář (co appka sbírá: účet, kontakty, poloha? —
     vyplníme pravdivě).
   - **Content rating** dotazník.
   - **Target audience** (dospělí / zaměstnanci).
3. **Release → Testing → Internal testing → Create release**.
4. Nahrát **`app-release.aab`** → zvolit podpis (viz rozhodnutí v bodě 1).
5. **Testers**: vložit e-maily zaměstnanců (až 100) nebo Google skupinu.
6. **Rollout** → testeři dostanou odkaz → nainstalují **čistě z Play**,
   žádný „neznámý zdroj".

---

## 4. Co dělá kdo

| Krok | Kdo |
|---|---|
| Play Console org účet + $25 + D-U-N-S verifikace | **Marti** |
| AAB build (`bundleRelease`, stávající klíč) | **Claude** (build bridge) |
| Privacy policy stránka `/privacy` | **Claude** |
| Data safety / content rating / listing | **Claude + Jirka** (Marti schválí) |
| Seznam e-mailů zaměstnanců pro testery | **Marti / Šárka** |
| Pozvat tým do Play Console | **Marti** |

---

## 5. Po vydání

- **Update appky** = nahrát novou AAB do Internal testing → testeři dostanou
  update automaticky z Play (konec ručního rozesílání APK!).
- **Closed/Open/Production** později, kdyby bylo třeba širší distribuce.
- **Převod na STRATEGIE - System** až bude mít vlastní D-U-N-S — Google
  přenese appku včetně hodnocení, statistik, testerů.

---

## 6. Srovnání Apple vs. Google (pro přehled)

| | Google Play | Apple |
|---|---|---|
| Cena | **$25 jednou** | $99 / rok |
| Účet | Organization + D-U-N-S (EUROSOFT) | Organization + D-U-N-S (EUROSOFT) |
| Interní rozdání | Internal testing (100 lidí, hned) | TestFlight |
| Podpis | náš `strategie-release.jks` | Apple certifikáty |
| Převod na STRATEGII | ✅ podporováno | ✅ podporováno |

---

## 7. Tahák na povinné formuláře (vyplníme, až bude účet ověřený)

### Privacy policy — ✅ HOTOVO
- URL: **`https://strategie-ai.com/privacy`** (nasazeno 8. 6., commit e9ffe16).

### Data safety (co appka sbírá — vyplnit pravdivě)
| Údaj | Sbírá? | Účel | Sdíleno 3. straně? |
|---|---|---|---|
| Jméno, e-mail, role | Ano | Funkce appky (účet) | Ne |
| Telefonní číslo | Ano | Funkce appky, ověření | Ne |
| Kontakty | Ano | Caller-ID (firemní adresář) | Ne |
| Audio (mikrofon) | Ano (jen na vyžádání) | Hlasová zpráva → přepis | Ne |
| Poloha (přesná) | Ne | — | — |
| Síťová přítomnost | Ano | Evidence přítomnosti | Ne |
| SMS | Jen brána, ověřovací | Ověření zařízení | Ne |
- **Šifrování při přenosu:** Ano (HTTPS).
- **Možnost požádat o smazání dat:** Ano (kontakt správce).
- **Žádná reklama, žádný prodej dat.**

### Content rating (dotazník)
- Kategorie: **Utility / Business** (firemní nástroj).
- Žádné násilí, sex, hazard, drogy → výsledek bude „Everyone / 3+".

### Target audience
- **Dospělí (18+)** — pracovní nástroj pro zaměstnance, ne pro děti.

### Store listing (i pro Internal testing minimální)
- **Název appky:** STRATEGIE
- **Krátký popis:** Interní firemní aplikace EUROSOFT - System (docházka,
  komunikace, pracovní informace).
- **Plný popis:** Aplikace pro zaměstnance EUROSOFT - System s.r.o. —
  evidence docházky, interní komunikace, firemní kontakty a notifikace.
  Není určena veřejnosti.
- **Ikona / grafika:** použít stávající ikonu appky (logo „S").

### ⏳ AAB build — záměrně až těsně před nahráním
- `bundleRelease` auto-zvýší verzi, a AAB stejně nejde nahrát před ověřením
  účtu → build uděláme, **až bude účet schválený a appka v Play založená**.
  Klíč `strategie-release.jks` je připravený.

---

*Připravil Claude (id=23), 8. 6. 2026. Doprovod: `apple_app_priprava.md`,
`apple_jirka_navod.md`.*
