# 📋 Google Play — připravené texty k vložení + analýza pravidel

> Připravil Claude pro Jirku, 25. 6. 2026. Doplněk k `google_play_priprava.md`.
> Účel: až bude Play Console účet schválený, jen **vkopírovat** do formulářů.
> Nic se tímto nenasazuje — je to čistě příprava textů.

**Ověřený stav appky k 25. 6. 2026:**
- `applicationId` = `cz.strategie.mobile`
- verze = **1.68 / versionCode 69** (auto-bump při release buildu)
- minSdk 26, targetSdk 36
- ikona ✅ hotová (adaptivní, všechny velikosti)
- zásady soukromí ✅ živé: `https://strategie-ai.com/privacy`
- appka pro iOS i Android = **stejný obsah** (společný web `/mobile`)

> ### 🌍 CÍL = VEŘEJNÉ (KOMERČNÍ) VYDÁNÍ
> Rozhodnutí Jirka 25. 6. 2026: stejně jako iOS chceme i **Android appku v Google
> Play jako VEŘEJNÝ produkt** — celý projekt včetně mobilní appky budeme nabízet
> dalším zákazníkům. Z toho plyne, jak jednáme:
> - **Účet = Organization** (vystupuje jako firma), profil + listing budou veřejné.
> - **Listing píšeme jako komerční B2B produkt** (ne „interní appka EUROSOFTu").
> - **Část 0 níže (samo-update, SMS/call-log) je POVINNÁ k vyřešení** — u veřejné
>   appky to nelze odložit, Google by produkci jinak odmítl.
> - **Rollout:** i veřejnou appku vydáme přes testovací track (Internal/Closed
>   testing) jako bezpečný mezikrok, pak teprve povýšíme na **Production (veřejné)**.

---

## ⚠️ ČÁST 0 — POVINNÉ pro veřejné vydání: dvě věci, které Google Play hlídá

Tohle je nejdůležitější sekce. Pro **veřejnou produkci** se obě věci **MUSÍ**
ošetřit (na testovacím tracku by sice prošly, ale cíl je veřejné vydání).
Řešení = **dvě varianty buildu**: čistá **Play (veřejná)** verze a interní
**sideload** verze pro firmu, která si náročné funkce nechá.

### A) Samo-aktualizace (stahování APK) — Play to ZAKAZUJE
- Appka teď umí stáhnout si novou APK a nainstalovat se sama
  (`installUpdate()` + oprávnění `REQUEST_INSTALL_PACKAGES`).
- **Pravidlo Google Play:** appka z Play se NESMÍ aktualizovat jinak než přes Play.
- **Co s tím:** pro Play verzi appky **vypnout tlačítko/funkci samo-update**
  a odstranit oprávnění `REQUEST_INSTALL_PACKAGES`. Aktualizace pak řeší Play sám.
- **Jak:** udělat „Play" variantu buildu (build flavor) bez self-update, nebo
  schovat tu funkci za přepínač. → úkol pro Claude **až těsně před Play buildem**
  (krok 5). Sideload verze pro firmu může self-update klidně mít dál.

### B) Oprávnění SMS a Call Log — Play je silně omezuje
- Appka má: `READ_SMS`, `SEND_SMS`, `RECEIVE_SMS`, `READ_CALL_LOG`.
- **Pravidlo Google Play:** tyto skupiny smí používat hlavně appka nastavená jako
  výchozí pro SMS/telefon. Jinak je třeba **schválený výjimečný účel** — jinak
  Play produkční verzi odmítne.
- **Pro veřejné vydání (náš cíl):** SMS/call-log skupiny smí veřejně používat
  hlavně appka nastavená jako výchozí SMS/telefon. Výjimku (Permissions
  Declaration) pro běžnou business appku Google **většinou neudělí**.
- **Doporučené řešení:** SMS bránu + protokoly hovorů do **veřejné Play verze
  NEDÁVAT**. Zůstanou jen v **interní sideload verzi** pro firemní „bránový"
  telefon (1 zařízení). Veřejní zákazníci tyto funkce nepotřebují.

> **Závěr:** veřejná Play verze = **čistý build** bez samo-update, bez SMS brány,
> bez čtení call-logu (a bez příslušných oprávnění). Interní firemní sideload
> verze si je nechá. Mikrofon (diktování), kontakty pro caller-ID a notifikace
> ve veřejné verzi zůstat mohou. Rollout: testovací track → pak Production.

---

## ČÁST 1 — Store listing (název a popisy)

> Listing píšeme jako **komerční B2B produkt** (appka pro firmy, ne „interní
> appka EUROSOFTu"). Appka vyžaduje firemní účet — to je u B2B appek běžné a OK.

**App name (povinné, max 30 znaků):**
```
STRATEGIE
```

**Short description (povinné, max 80 znaků):**
```
Podnikový systém pro firmy: docházka, lidé, komunikace a AI asistent.
```

**Full description (povinné, max 4000 znaků):**
```
STRATEGIE je moderní podnikový systém pro firmy — docházka, řízení lidí, interní
komunikace, firemní informace a AI asistent v jedné aplikaci. Mobilní appka je
součástí platformy STRATEGIE a propojuje zaměstnance s firemními procesy odkudkoli.

Co STRATEGIE umí:
• Evidence docházky (příchod, odchod, přehledy, samopotvrzení)
• Řízení lidí a týmů, firemní struktura
• Interní komunikace a notifikace
• Firemní kontakty s rozpoznáním volajícího (caller-ID)
• Pracovní přehledy, dokumenty a informace
• AI asistent pro každodenní agendu

Aplikace je určena firmám a jejich zaměstnancům. Pro používání je potřeba účet
ve STRATEGII (firemní přístup). Veškerá data jsou přenášena zabezpečeně (HTTPS).

STRATEGIE je produkt, který nasazujeme i u dalších firem — pokud máte zájem o
podnikový systém pro vaši firmu, ozvěte se na strategie-ai.com.
```

> ⚠️ Pozn.: stránka zásad `/privacy` dnes uvádí „appka není určena veřejnosti".
> Pro komerční vydání ji sjednotit s tímto B2B positioningem (úkol s Martim) —
> formulace „appka pro firmy, vyžaduje firemní účet" místo „interní, ne pro veřejnost".

**App category:** `Business`
**Tags:** business, productivity (interní nástroj)
**Contact email (povinné, zobrazí se):** `m.pasek@eurosoft.com`
**Website:** `https://strategie-ai.com`
**Privacy policy URL:** `https://strategie-ai.com/privacy`

> Grafika (povinné i pro testing): ikona 512×512 (z naší ikony „S"),
> feature graphic 1024×500, aspoň 2 screenshoty telefonu. → připraví Claude/Jirka
> z reálných obrazovek appky (docházka, home).

---

## ČÁST 2 — Data safety (bezpečnost dat) — VYPLNIT PRAVDIVĚ

Play se ptá u každého typu dat: **sbírá se?** (= odesílá z telefonu na server),
**sdílí se s 3. stranou?**, **účel**, **povinné/volitelné**. Vše šifrované při
přenosu (HTTPS) = Ano. Prodej dat = Ne. Reklama = Ne.

| Typ dat | Sbírá (jde na server)? | Sdílí 3. straně? | Účel |
|---|---|---|---|
| Jméno | Ano | Ne | Funkce appky (účet) |
| E-mail | Ano | Ne | Funkce appky (účet, přihlášení) |
| Telefonní číslo | Ano | Ne | Funkce appky, ověření zařízení |
| ID uživatele | Ano | Ne | Funkce appky (identita) |
| Docházka / pracovní záznamy | Ano | Ne | Hlavní funkce (evidence) |
| Hlas (mikrofon) | Ano (jen na vyžádání) | Ne | Hlasová zpráva → přepis |
| Síťová přítomnost | Ano | Ne | Evidence přítomnosti |

**Položky, které je NUTNO před odesláním ověřit (závisí na tom, co appka reálně
posílá na server vs. jen čte v telefonu):**

| Typ dat | Pozn. k ověření |
|---|---|
| Kontakty (telefonní seznam) | Appka kontakty **čte v telefonu** pro caller-ID. Pokud se telefonní seznam **NEodesílá** na server → v Data safety se NEhlásí jako „sbíráno" (jen on-device přístup). **Ověřit, že se neuploaduje.** |
| SMS (obsah) | „Bránový" telefon přeposílá ověřovací SMS na server (`/app/sms-inbound`). Pokud to dělá jen 1 firemní telefon → v Play verzi to nejspíš nebude (viz Část 0-B). Pokud zůstane → hlásit „SMS zprávy: sbíráno, ověření". |
| Protokol hovorů (metadata) | Vize call-log → CRM posílá metadata hovorů. Pokud Play verze tuto funkci nemá → nehlásit. **Ověřit dle finální Play varianty.** |

- **Šifrování při přenosu:** Ano (HTTPS).
- **Uživatel může požádat o smazání dat:** Ano → `m.pasek@eurosoft.com` (je v zásadách).
- **Data se prodávají?** Ne. **Reklama?** Ne.

---

## ČÁST 3 — Content rating (dotazník hodnocení obsahu)

- Kategorie appky: **Utility / Productivity / Business** (firemní nástroj).
- Násilí: Ne · Sex/nahota: Ne · Vulgarita: Ne · Drogy/alkohol/tabák: Ne
- Hazard: Ne · Uživatelská komunikace mezi uživateli navzájem: (firemní chat —
  uvést pravdivě dle toho, zda spolu komunikují uživatelé) · Sdílení polohy: Ne
- **Očekávaný výsledek:** „Everyone / 3+".

---

## ČÁST 4 — Target audience & ostatní povinná prohlášení

- **Cílová skupina:** Dospělí 18+ (pracovní nástroj pro zaměstnance, ne pro děti).
- **Appka cílí na děti?** Ne.
- **Ads (obsahuje reklamu)?** Ne.
- **Government app?** Ne.
- **COVID-19 app?** Ne.
- **Financial features?** Ne (interní docházka/komunikace; mzdové podklady jsou
  jen pro zaměstnance, ne veřejná finanční služba) — uvést dle skutečnosti.

---

## ČÁST 5 — App content checklist (Play to chce vyplnit i pro testing)

- [ ] Privacy policy URL → `https://strategie-ai.com/privacy` ✅ hotovo
- [ ] Data safety formulář → Část 2
- [ ] Content rating dotazník → Část 3
- [ ] Target audience → Část 4
- [ ] Ads prohlášení → Ne
- [ ] News app? → Ne
- [ ] Store listing (název, popisy, grafika) → Část 1
- [ ] Aplikace přístup pro recenzenta (pokud Google bude chtít) → demo účet
      (stejný princip jako u Apple — login + heslo pro recenzenta)

---

*Tento dokument je příprava textů. Nic nenasazuje. Build AAB + řešení Části 0
(self-update, SMS/call-log) se dělá až těsně před nahráním (krok 5 plánu).*
