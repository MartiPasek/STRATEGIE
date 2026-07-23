# Siemens Mall / SiePortal — napojení na dostupnost a dodací termín dílů (OCI5)

Oblast: nabidky (souvisí s kalkulace-rozvadecu). Zdroj: e-mailové vlákno Marti ↔ Siemens, 20.–23.7.2026. Zapsal C23 (Cowork) 23.7.2026.

## Cíl (proč to řešíme)
Dostat do STRATEGIE **aktuální dostupnost + dodací termín** konkrétního dílu Siemens (dle **MLFB**) — data, která se v čase mění a jsou klíčová pro **kalkulace a nabídky**. Bez ručního vyhledávání kus po kuse v SiePortalu. Ceník máme aktuální a objednávky řešíme přes EDI/ERP2Mall → **nepotřebujeme dotahovat celý katalog ani ceny**, jen dostupnost a termín.

## Řešení = OCI (Open Catalog Interface)
- Pro SiePortal je API napojení možné **jen přes OCI**, verze **4.0 nebo 5**. Siemens doporučil **OCI5** — mělo by umět vrátit informaci o **dostupnosti** daného produktu.
- **Nastavení OCI5 je BEZ nákladů.** Siemens nastaví spojení ze své strany a zašle **uživatelské jméno + heslo + URL**, které si nastavíme u nás v systému. Pak otestujeme, zda vyhovuje.
- **EDI** spojení Siemens v systému nevidí, ale máme aktivní **ERP2Mall** (elektronické objednávky).

## OCI/cXML pole (co lze namapovat)
Klíčová pro nás:
- `NEW_ITEM-VENDORMAT[n]` = **MLFB** (identifikace dílu)
- `NEW_ITEM-LEADTIME[n]` = **DeliveryDate** (dodací termín)
- `NEW_ITEM-PRICE[n]` = CustomerPrice, `NEW_ITEM-PRICEUNIT[n]` = PriceUnit, `NEW_ITEM-CURRENCY[n]` = Currency
- `NEW_ITEM-QUANTITY[n]` / `NEW_ITEM-UNIT[n]` = množství/MJ, `NEW_ITEM-DESCRIPTION[n]` / `NEW_ITEM-LONGTEXT_n:132[]` = popis
Plný seznam 31 polí (kromě výše): CONTRACT, CONTRACT_ITEM, CUST_FIELD1-5, CUST_INFOGLOBAL(2), CUST_INFOPOSITION, CUST_PROJECTID, EXT_CATEGORY_ID, EXT_PRODUCT_ID, EXT_QUOTE_ID/ITEM, EXT_SCHEMA_TYPE, MANUFACTCODE, MANUFACTMAT, MATGROUP, MATNR, VENDOR, SERVICE.

## Kontakty (Siemens s.r.o., RC-CZ DI)
- **Eliška Holoubková** — e-commerce Professional, RC-CZ DI E-business and SAP support: `sap.ebusiness.cz@siemens.com` (hlavní kontakt pro nastavení OCI).
- Miroslav Strolený `miroslav.stroleny@siemens.com`, Valter Czyž `valter.czyz@siemens.com`, Martin Koželka `martin.kozelka@siemens.com`, Jakub Brejcha `jakub.brejcha@siemens.com` (RC-CZ DI S — obchodně-technické zázemí).
- INTERSOFT (budoucí stejné napojení): Branislav Mózer `branislav.mozer@intersoft-automation.cz`.

## Stav k 23.7.2026
- Odeslali jsme souhlas s nastavením OCI5 pro test + **žádost o přihlašovací údaje** (user/heslo/URL). Poprosili jsme, ať zpřístupní **celý rozsah polí**, my vše otestujeme a co nevyužijeme, necháme zpětně zneaktivnit.
- **Čekáme na credentials od Siemens.** Meeting možný, ale kvůli dovoleným až **začátkem srpna** — mezitím testujeme, jakmile přijdou přístupy.
- Do budoucna stejné napojení i pro **INTERSOFT**.
- TODO po přístupech: nastavit OCI5 u nás, ověřit programový dotaz na MLFB → LEADTIME (dostupnost/termín) bez interaktivního proklikávání; napojit na kalkulace/nabídky. Souvisí s párováním BOM→kalkulace (RegCis).
