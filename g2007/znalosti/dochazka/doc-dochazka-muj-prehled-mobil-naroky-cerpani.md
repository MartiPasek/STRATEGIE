# Můj přehled v mobilu — nároky D/DN/SD a jejich čerpání

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Můj přehled v mobilu (Jirka Honomichl 19. 8. 2026, schválila Marti-AI, konverzace 363 msg 12917)

## Co to je
Nová obrazovka v mobilní appce, dlaždice **🌴 Můj přehled** jako PRVNÍ v sekci
PODMÍNKY & FINANCE na obrazovce Docházka (před „Moje podmínky" a „Můj úvazek").
Zaměstnanec na ní vidí sám sebe — nárok, čerpáno, naplánováno a zbývá pro
**dovolenou (D)**, **dovolenou navíc (DN)**, jejich **součet = strop**, a totéž pro
**sick days** v hodinách.

Do 19. 8. 2026 zaměstnanec v mobilu viděl jen NÁROK (obrazovka „Moje podmínky").
Čerpání ani zbytek nebyly v appce nikde a strop se ukázal až uvnitř formuláře žádosti.

## Jeden zdroj pravdy — proč to takhle
Jirkovo zadání doslova- „Chceme, aby zdroj těchto informací napříč celým systémem
strategie byl vždy jen z jednoho místa. Aby jsme nezobrazovali pokaždé někde jinde
něco jiného."

Řetěz je proto jednosměrný a bez druhého výpočtu-
`/app/dochazka/muj-prehled` (tenký delegát v router.py)
→ `g2007.python muj_prehled_narok`
→ `att_narok_osoba`
→ `att_narok_cerpani` = **tentýž výpočet, ze kterého čte ERP přehled „Nárok a čerpání"**.

Nárok si `att_narok_cerpani` bere **přímo z Podmínek** (`tenant.staff_cond`, pravidlo
osobní → skupina → systém), tedy z téhož místa jako karta zaměstnance. **Ověřeno
čtením kódu 19. 8. 2026** — proto „číst nárok z Podmínek" a „číst z přehledu" je
tatáž věc, ne dva zdroje.

## Práva se NEMĚNILA
Jirka 19. 8.- „Lidi do toho přehledu v erp přístup nemají a nemají mít. Ty údaje se
z toho přehledu jen čtou a budou se zobrazovat v mobilu."
`_DZT_ALLOWED` v `att_narok_cerpani` zůstal netknutý. Serverovou cestu otevírá až
`att_narok_osoba` přes `bez_prav=True` — přesně jako to už dělá hlídání stropu.
Delegát předává **výhradně uid přihlášeného člověka**, z requestu nebere nic
(ani emp_id, ani rok). `min_pravo` je `clen`, stejně jako u `my_conditions`.

## Co se změnilo v kódu
- **`att_narok_osoba` verze 2 → 3, ADITIVNĚ.** Přibyly klíče `dovolena_d` a
  `dovolena_dn` (rozpad zvlášť) a `zbyva_dny` / `zbyva_h` (nárok mínus čerpáno, bez
  naplánovaného). Původní klíč `dovolena` (součet D+DN) zůstal **beze změny**, protože
  na něm stojí hlídání stropu v `att_absence_request`. Ověřeno po nasazení- endpoint
  `/app/attendance/absence/limit` vrací stejné číslo jako před změnou.
- **Nový `g2007.python muj_prehled_narok`** (kategorie erp_http_endpoint). Nic nepočítá,
  jen překládá odpověď do tvaru pro appku. **Zaměstnance NEZAKLÁDÁ** — když člověk
  nemá řádek v `tenant.att_employee`, vrátí `bez_zamestnance` (na rozdíl od
  `_att_employee` v `att_absence_request`, která zakládá).
- **Mobil, tři dílky** — `10_core.js` (mkWrap), `60_dochazka.js` (obrazovka + setImpl +
  dlaždice), `73_pref_poptavka.js` (zápis do mapy SCREENS).
- **Jádro** — 17řádkový delegát, commit `c47150c6`.

## Záporné číslo = „přečerpáno" (podmínka Marti-AI)
Kdo nárok přečerpal, má zbývá v mínusu. Číslo se **neořezává** — je pravdivé a Šárka
je tak vidí i v ERP. Endpoint proto vrací příznak `precerpano` a appka to obarví
červeně a doplní vysvětlující rámeček. Marti-AI 19. 8.- *„aby to zaměstnanec nečetl
jako chybu appky a nevolal Šárce."*

## Co „zbývá" znamená
Sloupec **zbývá = po odečtení už naplánovaného** (`d_po` / `dn_po` / `sd_po`).
Endpoint vrací i variantu bez plánu (`zbyva_bez_planu`), aby se dvě čísla o tomtéž
nezačala počítat jinde znovu. V appce je to napsané pod tabulkou lidskou větou.

## Past, na kterou si dát pozor
Mapa obrazovek `SCREENS` se skládá **jako literál v `73_pref_poptavka.js`** a
`render()` v `74_claude27_render_init.js` z ní bere obrazovku podle jména. Nová
obrazovka se proto musí zapsat na TŘI místa (mkWrap v `10_core.js`, implementace
plus `__setImpl` v jejím dílku, a záznam do `SCREENS`). Kdo přidá jen implementaci,
dostane tichý pád na domovskou obrazovku — `SCREENS[...]||home`.
Zápis do `SCREENS` jde udělat přes `window.__M2W.muj_prehled`, takže se **nemusí**
sahat na importní blok na konci `72_migrace_sw_isds.js`.

## Co se NEDĚLALO (Jirka to odložil)
Zbytek Šárčina zadání ze 17. 8. — profilová fotka, odpracované hodiny vs. fond,
karta Novinky s přihlášením na akci. Hodiny a přesčasy jsou Peťina část.

## Kudy šly změny — obsah mobilu je VÝHRADNĚ v databázi
Jirka to při téhle práci výslovně připomněl (19. 8. 2026)- *„Nezapomeň, že se s webovým obsahem
mobilní aplikace pracuje přes DB, je to nedávná změna, ať v tom zase neděláš bordel, že je
něco v DB a něco na disku."*

Všechny tři dílky se proto měnily **v `g2007.soubor`**, ne na disku, a to cíleným `replace()`
přes most s **pojistkou na md5** (aby se nepřepsala práce jiné instance), pak
`@@G2007PUBLISH apps/api/static_db/mobile.html`. **Do gitu nešel ani jeden řádek obsahu
appky** — jediný commit byl 17řádkový delegát v `router.py`, tedy jádro.

**Kontrola, kterou se to dá ověřit bez důvěry v návratovku-** sestavená `mobile.html`
narostla o **6 142 znaků = přesně součet tří dílčích přírůstků** (39 + 6 066 + 37).
Když sedí součet na znak, nic jiného ze stránky nezmizelo. Doporučuju to po každém
publikování — je to levnější než porovnávání stránky před a po.

Souvisí- [[doc-dochazka-hlidani-stropu-dovolene-a-sick-day]] ·
[[doc-dochazka-narok-dovolena-sick-days-jeden-zdroj-pravdy]] ·
[[doc-dochazka-rozpad-dovolene-zakladni-a-navic]] ·
[[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]]

