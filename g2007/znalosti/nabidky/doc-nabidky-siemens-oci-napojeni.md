# Siemens Mall / SiePortal — dostupnost a dodací termín (napojení STRATEGIE)

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Siemens Mall / SiePortal — dostupnost a dodací termín (napojení STRATEGIE)

## Kontext / cíl (upřesněno 22.7.2026)
EUROSOFT chce z STRATEGIE dotahovat od Siemensu data pro **tvorbu kalkulací a nabídek**.
**Ceny NEŘEŠÍME** — ceník Siemens máme aktuální u sebe. **Auto-objednávky NEŘEŠÍME** — máme s nimi EDI.
Jádro potřeby = **aktuální DOSTUPNOST + DODACÍ TERMÍN podle MLFB**, ideálně automaticky (dynamická data, mění se denně).

## Ověřeno v SiePortalu (22.7.2026, účet EUROSOFT-Control 1002384)
Přihlášený web účet u dílu dle MLFB reálně ukazuje: zákaznickou i listovou cenu, skladovost (in / not in stock) a **odhadovaný datum dostupnosti**.
Příklad 3RT2625-1BB45 (CONTACTOR): „Not in stock", dle standardní dodací doby dostupné **30.07.2026**; přesnější dodací info po vložení do košíku a přepočtu dostupnosti.
→ Dostupnost + termín tedy máme **ručně hned**, zdarma. Chybí jen automatizace. (Přístupové údaje k účtu do g2007 NEPATŘÍ — jen postup.)

## Možnosti napojení (od ruční po automat)
1. **Ruční SiePortal** — funguje teď. Dohledání dostupnosti a termínu u dílu. Pro pár položek OK.
2. **OCI (nabízí Siemens, Eliška Holoubková)** — pole `NEW_ITEM-LEADTIME` = DeliveryDate = přesně dodací termín; funkce VALIDATE vrací aktuální data pro díl. Ale OCI je interaktivní punch-out (VALIDATE = HTML auto-submit formulář, ne čisté API) → poloautomat.
3. **Dedikované availability rozhraní / EDI availability check** — k prověření u Siemensu; pro plnou automatizaci „MLFB → dostupnost+termín" bez člověka.
4. **Strojová e-mailová poptávka (request/response)** — STRATEGIE umí strojově odeslat e-mail s poptávkou na díly v libovolném formátu (seznam MLFB v CSV/XML/pevný text). Pokud to Siemens na své straně strojově zpracuje a automaticky odpoví dostupností + termínem, je to **nejjednodušší schůdná cesta** (bez OCI/nasazování). Závisí na tom, zda to Siemens umí.

## Stav (22.7.2026)
Odeslána odpověď Elišce Holoubkové (přes původní vlákno) se 3 dotazy: (a) umí OCI LEADTIME/VALIDATE dotazovat dostupnost+termín programově na pozadí, (b) mají dedikované availability/delivery rozhraní nebo EDI zprávu, (c) zvládnou strojovou e-mailovou poptávku a automatickou odpověď. Čeká se na vyjádření Siemensu.

## Klíčová otevřená otázka na Siemens
Protože ceník máme, nepotřebujeme celý OCI katalog — potřebujeme **aktuální dostupnost + dodací termín per MLFB**. Umí to OCI (LEADTIME/VALIDATE) dotazovat **programově na pozadí**, mají **dedikované availability/delivery rozhraní** (příp. EDI zprávu), nebo zvládnou **strojovou e-mailovou poptávku**? To rozhodne plná automatizace vs. poloautomat.

## OCI — technické detaily (referenční)
- OCI = punch-out, ne REST API; návratová pole `NEW_ITEM-*` naplní nákupní košík/požadavek v ERP.
- Relevantní pole: `NEW_ITEM-VENDORMAT` (MLFB) · `LEADTIME` (dodací termín) · `DESCRIPTION` · `UNIT` · `QUANTITY`. Dotaz na Siemens: lze přenášet i skladovou dostupnost/množství, ne jen LEADTIME?
- Verze OCI (4.0/5) necháme doporučit Siemensu dle možností STRATEGIE + ověřit podporu VALIDATE/Background Search.

## Kontakty (Siemens)
- Eliška Holoubková — e-commerce, sap.ebusiness.cz@siemens.com
- Miroslav Strolený — RC-CZ DI S TER (nabídl Teams call); v kopii Czyž, Koželka, Brejcha
- Login do SiePortalu poskytl Radek Hellmayer (EUROSOFT-Control).

## Zdroje
- Siemens Industry Mall — Link to your procurement system (OCI): https://mall.industry.siemens.com/help/ww/en/03_Orders/03_09_Connection_to_shop_system.htm
- SAP OCI 4.0 spec: https://punchoutcommerce.com/docs/sap-oci-4.pdf

