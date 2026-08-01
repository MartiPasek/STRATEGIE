# Siemens Mall / SiePortal — napojení přes OCI (pro nabídkové řízení)

**Oblast:** nabídky · **Slug:** siemens-oci-napojeni · **Vznik:** 22.7.2026 (C23 / Cowork, z rozboru odpovědi Siemensu)

## Kontext / cíl
EUROSOFT chce napojit interní systém STRATEGIE na katalog Siemens kvůli **tvorbě kalkulací a nabídek** — poslat z naší strany dotaz na konkrétní díl (dle MLFB) a dostat zpět potřebné hodnoty (cena, cenová jednotka, měna, dodací lhůta/dostupnost).
**Automatické objednávání NEŘEŠÍME** — na to máme se Siemensem EDI. OCI nás tedy zajímá čistě pro cenové/nabídkové dotahování.

## Co Siemens nabízí (odpověď Eliška Holoubková, e-commerce, 22.7.2026)
Napojení do SiePortalu přes API je aktuálně možné **jen přes OCI (Open Catalog Interface), verze 4.0 nebo 5**. Siemens ho nastaví na své straně, dá přihlašovací údaje + URL, které si nastavíme u sebe. Potřebují od nás vědět: **kterou verzi OCI** a **která pole** mapovat.

## Klíčové zjištění / gotcha — OCI ≠ REST API
OCI je ve své podstatě **interaktivní „punch-out" katalog, ne programové API.** Uživatel z našeho systému „proklikne" do SiePortalu, tam naplní košík, a OCI při návratu pošle položky (pole `NEW_ITEM-*`) zpět do **nákupního košíku / požadavku** v ERP. Siemens to sám popisuje jako „acquisition of shopping cart data into ERP systems."

- Pole `NEW_ITEM-*` = **návratová pole OCI košíku**. Míchají popis dílu (MLFB, popis, cena, jednotka, výrobce, materiálová skupina) **a** nákupní kontext (`CONTRACT`, `EXT_QUOTE_ID`, `CUST_PROJECTID`). Popisnou podmnožinu lze použít i k **založení skladové karty**, ale nativní účel je naplnit nákupní požadavek.
- Funkce **VALIDATE** a **BACKGROUND_SEARCH** ve spec OCI 4.0/5.0 existují, ALE:
  - `VALIDATE` pošle ID dílu + množství a katalog vrátí **HTML stránku s formulářem, který se přes JavaScript sám odešle** — určeno k **aktualizaci/refresh položky, kterou už máme na požadavku**, ne jako čisté „pošli MLFB → vrať cenu" API.
  - `BACKGROUND_SEARCH` vyžaduje, aby výslednou položku **vybral uživatel** (formulář se nesmí odeslat automaticky).
  - → Pro **plně automatizovaný dotaz na cenu/dostupnost na pozadí** není OCI ideální nástroj; zvládne to jen v poloautomatické podobě (člověk proklikne, ceny se vrátí do kalkulace).

## Doporučení / směr
Protože cíl je „dotaz na díl → cena + dostupnost pro kalkulace" a auto-objednávky řešíme přes EDI, stojí za zvážení zeptat se Siemensu, jestli **ceny/dostupnost nejdou přes EDI**, které s nimi už provozujeme (cenový katalog **PRICAT** nebo poptávkové zprávy) — bývá to na tohle čistší automatická cesta než OCI punch-out.

## Základní pole k mapování (Siemensem nabídnutá, nám vyhovují)
`NEW_ITEM-VENDORMAT` (MLFB) · `DESCRIPTION` · `LONGTEXT` · `PRICE` · `PRICEUNIT` · `CURRENCY` · `UNIT` · `QUANTITY` · `LEADTIME` (dodací lhůta).
Doplňující dotaz na Siemens: lze kromě `LEADTIME` přenášet i skladovou dostupnost/množství?

## Otevřené otázky (k dořešení)
1. **„Klasický přístup k Siemens Mall od Radka"** — co přesně obsahoval? Pokud běžný **web login do SiePortalu**, přihlášený uživatel si u každého MLFB ručně vytáhne zákaznickou cenu i dostupnost → pro tvorbu kalkulací to fakticky může stačit i bez OCI (jen ručně).
2. **Verze OCI** — necháme doporučit Siemensu dle možností našeho ERP (STRATEGIE), a ověříme, která podporuje VALIDATE / Background Search.
3. **EDI cenový katalog** jako alternativa k OCI pro automatizaci cen.

## Kontakty (Siemens)
- Eliška Holoubková — e-commerce Professional, `sap.ebusiness.cz@siemens.com` (RC-AT DI FIN PC PRX, Ostrava)
- Miroslav Strolený — RC-CZ DI S TER (předává požadavek), nabídl Teams call
- V kopii: Valter Czyž, Martin Koželka, Jakub Brejcha

## Zdroje
- Siemens Industry Mall — „Link to your procurement system" (OCI): https://mall.industry.siemens.com/help/ww/en/03_Orders/03_09_Connection_to_shop_system.htm
- SAP Open Catalog Interface (OCI) Release 4.0 (spec): https://punchoutcommerce.com/docs/sap-oci-4.pdf
