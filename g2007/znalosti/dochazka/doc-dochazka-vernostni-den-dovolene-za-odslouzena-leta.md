# Věrnostní den dovolené za odsloužená léta — pravidlo, automat a evidence

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Věrnostní den dovolené za odsloužená léta

**Pravidlo potvrdil Jirka 14. 8. 2026:** +1 den dovolené navíc za **každých deset let ve firmě** — po 10, 20, 30, 40 a dál, dokud u nás člověk pracuje. **Roky musí být odpracované V KUSE.** Zapsal Claude-28, 14. 8. 2026, schválila Marti-AI.

## Kde to žije

- **Automat**: g2007.python `att_vernost_dovolena` (delegát `_hr_vernost_dovolena` v router.py), běží 1×/den ze smyčky att_sync. Den připisuje do `tenant.staff_cond` (`dovolena_dni`), notifikaci posílá jen Šárce (13).
- **Evidence**: `tenant.vernost_dovolena_log`, UNIQUE (tenant_id, user_id, roky_ve_firme) — pojistka proti druhému přidání na úrovni databáze.
- **Zobrazení**: karta zaměstnance pod „Podmínky (aktuálně platné)", blok „🎖️ Věrnostní dny dovolené navíc". Kdo nemá záznam, bloku nevidí.

## Jak se počítají odsloužená léta (od 14. 8. 2026)

Hledá se **poslední souvislý blok smluv**, ne nejstarší nástup:
1. Blok se láme, když je mezi koncem předchozí smlouvy a začátkem další **víc než 31 dnů** (kratší mezera = přechod mezi smlouvami, ne odchod z firmy).
2. Souvislost se posuzuje přes **všechny smlouvy včetně dohod** — jinak by pár měsíců brigády mezi dvěma hlavními poměry udělalo umělou díru. **Erika Sedláčková** měla 2010 mezi HPP tři měsíce DPP a podle Jirky u nás nikdy neskončila; správně jí vychází 17 let od roku 2008.
3. **Začátek let** se ale bere od první **nedohodářské** smlouvy v tom bloku — dohoda odsloužená léta nezakládá. Jirka 14. 8. 2026: *„Roky odpracované jako DPP jednoznačně nezapočítávat do těch deseti let."* **Michelle Šafránková** má proto 8 let od HPP (2018), ne 12 od letních brigád (2014–2017), a den dostane až v roce 2028.
4. Konec smlouvy s nevyplněným datem: u současné = dnes, u staré = začátek následující smlouvy (staré verze mají `smlouva_do` často prázdné a tvářily by se, že běží dodnes — právě na tom se past odhalila).

**Petr Beneš** je důvod, proč pravidlo vzniklo: smlouvy 2014-11-01 až 2019-06-28, pak **přestávka 5,5 roku**, znovu až od 2025-02-01. Jirka: *„Petr Beneš nepracoval ve firmě 10 let v kuse."* Nárok mu tedy nevznikl (Centrála mu drží 25 dnů, ostatní se srovnatelnou dobou mají 26). V evidenci má záznam se `zdroj='nevznikl'` a `pridano_dnu=0`.

## Kdo nárok NEMÁ (rozhodl Jirka 13.–14. 8. 2026)

- **dohodáři** (DPP/DPČ)
- **jednatelé** (Marti Pašek, Branislav Mózer)
- **vedoucí zakázek** — všichni s tímto postem včetně Mirka Mareše, který je vede
- Post se čte z NAŠÍ org struktury (`tenant.org_post_assign`), do Centrály se nekouká. Posty Ondry (9007) a Mareše (9005) byly 14. 8. doplněny ručně podle Centrály.
- „Brigádník Saxana" (číslo 208) nemá pracovní poměr vůbec — je ve STRATEGII jen kvůli docházce, do výběru nespadne sám od sebe.

## Historie: proč pojistka vznikla

Původní automat (Šárka 5. 8. 2026) přidával den jen přesně v desátém roce a jako pojistku bral existenci entitlementu. To neumělo rozlišit druhé výročí od prvního a hlavně **nevidělo, že Šárka den zadala rovnou do Centrály** — proto ho pět lidí (Havlát, Honomichl, Honal, Kilberger, Veverka) dostalo dvakrát a 13. 8. 2026 se to opravovalo ručně.
Evidence byla 14. 8. naplněna historií 15 lidí, kteří výročí už dosáhli, jinak by přepsaný automat den přidal znovu. **Jan Svoboda** (souvisle od 2015-01-01, výročí 1. 1. 2025) den nikdy nedostal — doplněn ručně 14. 8. 2026 na pokyn Jirky, dovolená v Podmínkách zvýšena z 25 na 26.

**Pozor při čtení čísel:** věrnostní dny jsou **už zahrnuté** v celkové hodnotě dovolené v Podmínkách, nepřičítají se k ní. Proto je v přehledech u čísla jen medaile, ne „+1" — to vypadalo jako přičtení a mátlo.

Souvisí: [[doc-dochazka-narok-dovolena-sick-days-jeden-zdroj-pravdy]]

