# Opravy docházky — chování přehledu, detailu a historie (stav 22.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Modul **Opravy docházky** (`apps/api/static/dochazka-opravy.html` + endpointy `/app/attendance/fix/*` v `modules/erp/api/router.py`). Editor opravuje cizí docházku ve své působnosti. Tento dokument = chování UI po vlně úprav Peťa+Claude‑26 21.–22. 7. 2026. Vše NASAZENO.

## Fronta „K vyřešení" (levý sloupec)
- Dvě sekce: **✋ Rozporované dny** (co hlásí lidé) a **⚠ Nesrovnalosti (automatická kontrola)** = anomálie.
- Po opravě položka **NEZMIZÍ hned** — zůstane zeleně „✓ opraveno" s tlačítkem **✓ Hotovo — z fronty**, maže se AŽ odkliknutím (parita s rozpory od lidí). Dřív anomálie po opravě/stornu zmizela (auto‑resolve v fix‑endpointech + filtr `e.status<>'superseded'`); auto‑resolve zrušen, filtr uvolněn pro opravené dny do 60 dnů.
- **Staré opravené (>60 dnů)** se z fronty skryjí, ale dole svítí drobné **červené** upozornění „N opravených nesrovnalostí starších 60 dnů čeká na odkliknutí" + rozbalení s tlačítkem Hotovo (aby se nedaly „ztratit").
- Karta, jejíž den je otevřený vpravo, je **modře zvýrazněná** („👁 otevřeno vpravo") — proti překliknutí.
- Po odbavení karty (V pořádku / Hotovo) se **zavře i detail vpravo**, pokud patřil té kartě.

## Detail dne (pravý panel)
- Nahoře panely: **✋ Co člověk hlásí** (oranžově) a **⚠ Co systému nesedělo** (červeně) = nevyřešené anomálie dne; k hlášce se ve stejném okénku ukáže i **poznámka ze záznamu** (auto‑odhlášení, zkráceno uživatelem…), ať je hned jasné, že už je den upravený.
- Hodiny v **desetinné (setinné) soustavě** (5,90 = 5 h 54 min), časy od–do zůstávají hodinové.
- **∑ Součet dne**: Odpracováno (bez přestávek) → „… z toho nad fond (nenárokové)" (počítá se z odpracováno vs denní fond `resolve` z engagement/kategorie, ukáže se i než automat řádek dopíše) → jednotlivé nepřítomnosti (Dovolená…) na vlastních řádcích → Celkem → Přestávky mimo součet.
  - **Nenárokové NENÍ hodiny navíc** — je to ČÁST odpracovaných hodin nad fond, do součtu se nepřičítá.
  - **Přestávka** se odečítá jen tou částí, která leží UVNITŘ pracovního záznamu (rozdělená práce → pauza v mezeře se neodečítá). Stornované přestávky se nepočítají.
- Řádek **Celkem** přímo v tabulce dne (ne jen dole).
- Typy v roletce opravy: Práce, Home office, Cesta, Pauza + nepřítomnosti **Dovolená / Lékař / Sickday / Neplacené volno**. **Režie NENÍ typ — je to zakázka** (práce na režii = typ Práce + zakázka Rezie). „🫡 Odchod" (day_end) se v přehledu vůbec nezobrazuje (v mobilu zůstává jako „Mám volno").
- Nepřítomnost jde ve výkazu na zakázku **Režie** s vlastní činností (Dovolená…), mapa `_ATT_ABS_CINNOST`, činnosti skupiny `vyroba_cinnost.kind='nepritomnost'` (lidem se v mobilu nenabízejí).

## Historie oprav
- Přehledné karty s barevnými štítky (✏️ Oprava, 🗑 Storno, 🔗 Sloučení, ✓ Vyřízeno, 🔒 Zámek), změna jako před→po.
- U každé položky tlačítko **🛠 Otevřít den — opravit** → otevře den vpravo, dá se hned opravit. Den se u „Vyřízeno" (resolve) dopočítá ze záznamu (`COALESCE(old_entry_date, entry_date záznamu)`), aby tlačítko bylo i tam.
- Endpoint `/app/attendance/fix/audit` vrací i `user_id` (kvůli otevření dne).

## Gotchy
- Bridge read‑guard bere `'add'` v `action IN (...)` jako DDL klíčové slovo ADD → dotaz spadne na „forbidden keyword". Řešení: `action NOT IN ('period_lock','period_unlock')`.
- Cloud deploy občas vrátí přechodné HTTP 401 („Nejsi přihlášen") — commit+push projdou, jen nahrání selže; opakovat, napodruhé/napotřetí projde.

