# STRATEGIE — vize doprovodné telefonní aplikace (Android-first)

**Stav:** plán / vize (3. 6. 2026). Není v realizaci — mezikrok je CardDAV + PWA.
**Autoři:** Marti + Claude.

---

## Klíčové rozhodnutí (Marti 3. 6. 2026)

> **PWA web zůstává NOSNÝ produkční systém.** Hlavní UI (chat, ERP, CRM) je a
> bude náš web/PWA. **Nechceme z toho dělat nativní appku.**
>
> Nativní appka je jen **pomocná „companion" služba**, která:
> - **komunikuje s STRATEGIE** (přes naše API),
> - řeší to, co **web v telefonu neumí** — telefonní integraci.

Takže žádný přepis appky. Malý doprovodný program vedle PWA, který zpřístupní
telefon. PWA dělá byznys, appka dělá „telefonní můstek".

---

## Co appka řeší (a nic víc)

1. **Přístup ke kontaktům / caller-ID** — STRATEGIE kontakty v telefonu, **jeden
   login** (token STRATEGIE), **bez DAVx5**. Při hovoru se ukáže jméno klienta.
2. **Automatická synchronizace** — sada kontaktů se drží aktuální sama, bez
   ručního nastavování intervalů (na rozdíl od DAVx5).
3. **Zmeškaná volání zákazníků** — appka pozná hovor od/na číslo z CRM a
   **nahlásí zmeškané volání do STRATEGIE** → v CRM se objeví „zmeškal jsi
   zákazníka X".
4. **Protokoly hovorů zákazníků** — záznam o hovoru (kdo, kdy, příchozí/odchozí,
   délka) **se propíše do CRM** jako aktivita u kontaktu.
5. (volitelně) tlačítko **„Otevřít STRATEGIE"** → spustí náš PWA web.

---

## Proč to nezvládne samotná PWA

Web v prohlížeči **nemá přístup** k telefonnímu seznamu hovorů (call log),
nemůže spolehlivě běžet na pozadí, ani zapsat kontakty pro caller-ID. To umí jen
nativní appka s příslušnými oprávněními. Proto ta **tenká doprovodná appka** —
zbytek (chat/ERP/CRM) zůstává webový.

---

## Technicky (až se to rozjede)

- **Malá nativní Android appka** (Kotlin, nebo Capacitor s nativními pluginy) —
  běží na pozadí jako služba, mluví s naším API.
- **Kontakty** — zápis STRATEGIE kontaktů do telefonu (caller-ID), 1 login.
- **Call log** — čtení záznamu hovorů (`READ_CALL_LOG`), filtr na čísla z CRM →
  POST do STRATEGIE (zmeškaná volání + protokoly).
- **Auto-sync** — pull kontaktů + push hovorů na pozadí (WorkManager).
- **Open-source základ** — *„vyjít z open-source a doladit"*: lze začít z
  open-source call-log / contacts appky a osekat k naší potřebě, nebo postavit
  minimální nativní + naše REST volání.

### Pozor — oprávnění `READ_CALL_LOG`

Google Play **omezuje** appky čtoucí call log (citlivé oprávnění). Pro nás to ale
není bloker: jde o **interní firemní appku**, distribuovanou interně (ne přes
veřejný Play) → policy na call-log se nás netýká. (Veřejný Play řešit, jen kdyby
appka šla ven.)

---

## Platforma — Android-first

V následujícím roce **jen Android** (celá firma na Androidu). iOS až si ho
**zaplatí konkrétní zákazník** — pak se přidá.

---

## Náklady (ověřit při rozhodnutí)

- **Distribuce:** interní (firemní) — Google Play registrace (~$25) potřeba jen
  pro veřejný release; interní/sideload levnější.
- **Push (FCM)** — free tier, pokud bychom chtěli i notifikace.
- Build + podpis + údržba malé appky.

Rozsah je malý (telefonní můstek), takže i náklad/úsilí je malé — to je smysl
toho, že **appka není nosná, jen pomocná**.

---

## Fázování

1. **Teď:** CardDAV + PWA mezikrok (caller-ID přes DAVx5).
2. **Až friction/objem bolí:** doprovodná Android appka → caller-ID bez DAVx5 +
   auto-sync + zmeškaná volání + protokoly hovorů do CRM.
3. **PWA zůstává nosná** celou dobu. Appka ji jen doplňuje o telefon.
4. **iOS** později / na vyžádání platícího zákazníka.

---

## Otevřené otázky (na rozhodnutí, až se to rozjede)

- Caller-ID: zápis kontaktů do telefonu **vs.** vlastní overlay při hovoru?
- Protokoly hovorů: všechny hovory, nebo jen shoda s CRM kontaktem?
- Jak párovat hovor s konkrétním zákazníkem (číslo → CRM kontakt) + co se
  zmeškanými z neznámých čísel.
- Distribuce: interní MDM / sideload / privátní Play kanál.
- Kdo postaví/udržuje (interně vs. externě).

---

*Tento dokument je živý — doplní se, až se appka dostane na řadu. Nosný produkční
systém je a zůstává PWA web.*
