# Pro Marti-AI — nová e-mailová šablona „Automatický e-mail DE" (Pavlova německá nabídka)

Od Kristý + Claude-24, 19. 6. 2026. Cíl: založit do `dbo.EC_KontaktMailSablonyCis` novou
šablonu **„Automatický e-mail DE"**, aby šla vybrat v „Oslovit vybrané". Stejný princip
jako tvoje šablona OTEVÍRÁK (ID 9) — HTML tělo + **inline obrázky přes `cid:`**.

> ## ⭐ HOTOVÝ PODKLAD (Claude-24, 22. 6. 2026)
> `.msg` jsem už rozebral a připravil **ready-to-insert HTML tělo**:
> **`docs/mail_sablony/automaticky_email_DE_FINAL.html`** — to vlož přímo do sloupce `Sablona`.
> - `cid:` odkazy už sedí (de-encapsulováno z RTF, cp1250, hotové).
> - **Přeposílací blok odstraněn** (Pavlovo CZ „Přeposílám…" + From/Sent/To/Subject).
> - **Oslovení anonymizováno** na „Sehr geehrte Damen und Herren," (potvrdila Kristý 22.6.).
> - **Použito 14 obrázků: `image001`–`image014`** (skupina cid `@01DCD717.C657E160`),
>   všechny v `docs/mail_sablony/de_images/` (ověřeno byte-identické). **image015–019 NEpoužívej** —
>   patřily k Pavlově přeposílací CZ části, kterou jsme odstranili.
> - Náhled (obrázky vložené jako data-URI, jen ke kontrole): `docs/mail_sablony/nahled_DE_FINAL.html`.
>
> Takže tvůj jediný krok = **INSERT** (HTML z FINAL + 14 inline příloh s jejich Content-ID). Detaily níže.

## Zdroj = .msg (jediný konzistentní zdroj)
Pavel dodal zatím jen **německou** variantu. Kristý ji nahrála jako `.msg`
(„FW: Kooperationsangebot…"). **Pozor:** Outlookový `.htm` export číslоval obrázky jinak
(+ VML fallback odkazy), takže `.htm` tělo a `.msg` přílohy se nespárují. **Použij `.msg`** —
tělo (RTF-encapsulated HTML) i přílohy patří k sobě. (Claude může `.msg` přiložit / Kristý
ti ho předá v chatu.)

## Předmět
`Kooperationsangebot: Unterstützung im Bereich Elektrokonstruktion und Automatisierung`
(bez „FW: ").

## Obsah (text)
Německá nabídka spolupráce (Elektrokonstruktion / E-Planung / Schaltschrankbau),
EUROSOFT-Control s.r.o., 20 let zkušeností v DACH, reference ISIMAT, SIEMENS, Polytechnik,
Junker, BMW, Audi, VW + Pavlův podpis (Dipl.-Ing. Pavel Zeman, Business Manager,
pavel.zeman@eurosoft.com, +420 739 709 870, ENX/TISAX AL2).

## Obrázky — POUŽÍT JEN 14 (image001–014), cid mapa z .msg
**Aktualizace 22.6. (Claude-24):** po odstranění přeposílacího bloku zůstává v německé
nabídce referencovaných **jen 14 obrázků** — `image001`–`image014` (skupina `@01DCD717.C657E160`).
**image015–019 (`@01DCFF1B.83980450`) NEpoužívej** — patřily k Pavlově CZ přeposílací části.
Plné cid hodnoty pro těch 14 jsou v `automaticky_email_DE_FINAL.html` (sloupec `src="cid:…"`).

Content-ID skupiny (původní úplný výpis z .msg, pro referenci):
- `image001.jpg`–`image014.*` → `@01DCD717.C657E160`  ← **TYTO použít**
- `image015.png`–`image019.jpg` → `@01DCFF1B.83980450`  ← nepoužívat (CZ forward)

Konkrétně (jméno | cid | velikost):
```
image001.jpg image001.jpg@01DCD717.C657E160 10103
image002.jpg image002.jpg@01DCD717.C657E160 16936
image003.jpg image003.jpg@01DCD717.C657E160 17602
image004.jpg image004.jpg@01DCD717.C657E160 23851
image005.jpg image005.jpg@01DCD717.C657E160 19865
image006.png image006.png@01DCD717.C657E160 3392
image007.jpg image007.jpg@01DCD717.C657E160 17379
image008.png image008.png@01DCD717.C657E160 1841
image009.png image009.png@01DCD717.C657E160 1788
image010.png image010.png@01DCD717.C657E160 1802
image011.png image011.png@01DCD717.C657E160 1317
image012.jpg image012.jpg@01DCD717.C657E160 4727
image013.png image013.png@01DCD717.C657E160 63290
image014.jpg image014.jpg@01DCD717.C657E160 529
image015.png image015.png@01DCFF1B.83980450 14398
image016.png image016.png@01DCFF1B.83980450 11909
image017.png image017.png@01DCFF1B.83980450 41573
image018.png image018.png@01DCFF1B.83980450 61603
image019.jpg image019.jpg@01DCFF1B.83980450 681907
```
(Claude má 19 obrázků vytažených z .msg — pokud je chceš, předá je; jinak si je vytáhneš z .msg sama, je to čistší.)

## Co je potřeba udělat (Marti-AI) — zjednodušeno, podklad hotový
1. ✅ HOTOVO Claude-24: HTML tělo je v **`automaticky_email_DE_FINAL.html`** (RTF→HTML
   de-encapsulace, přeposílací hlavička pryč, oslovení anonymní). **Vezmi ho jako `Sablona`.**
2. **Inline přílohy = 14 obrázků** `image001`–`image014` (z `docs/mail_sablony/de_images/`)
   s Content-ID skupiny `@01DCD717.C657E160` (stejný princip jako OTEVÍRÁK `cid:20let_cz.png`).
   Plné `cid` hodnoty jsou přímo v `src="cid:…"` ve FINAL HTML. **image015–019 vynech.**
3. **INSERT** do `dbo.EC_KontaktMailSablonyCis`: `Nazev='Automatický e-mail DE'`,
   `Sablona=<obsah automaticky_email_DE_FINAL.html>`, `Autor='Pavel'` (nebo `'Marti-AI'`),
   `Poradi=7` (poslední stávající je ID 15 s `Poradi=6`).
4. Merge pole: žádná — oslovení je už **„Sehr geehrte Damen und Herren,"** (anonymní,
   potvrdila Kristý 22.6.). Tělo nech jak je.

> Pozn. k odeslání: u `send_email` namapuj 14 příloh na jejich `cid` (Content-ID v hlavičce
> přílohy = hodnota za `cid:` ve `src`), aby se zobrazily inline — stejně jako u OTEVÍRÁKu.

## Co udělal Claude-24 ✅ (HOTOVO 22. 6. 2026, commit 905c080d)
- Výběr šablony v „Oslovit vybrané" se teď **načítá dynamicky** z číselníku
  `dbo.EC_KontaktMailSablonyCis` (nový read endpoint `GET /crm/osloveni/sablony`,
  dropdown v `erp_grid_actions.js` přes fetch, fallback 9/10).
- **Důsledek pro tebe:** jakmile vložíš „Automatický e-mail DE", objeví se ve výběru
  **sama** — žádná další úprava UI není potřeba. Tvůj INSERT je poslední krok.

## Pozn.
- Zatím existuje jen DE varianta. CZ doplníme, až ji Pavel dodá.
- Ostré odesílání pořád čeká na právní OK; na DE firmy Pavel zatím neposílá.
