# Mobil: obrazovka "Moje docházka" postavena nad zdrojem ERP Oprav docházky, pět starých dlaždic zrušeno (13. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

Zadal Jiří Honomichl 13. 9. 2026, schválila Marti-AI (msg 15418, 15427, 15437, 15441, 15447). Provedl Claude-28.

## Co se změnilo

Obrazovka `moje_dochazka_b` (do té doby záměrně prázdná) dostala obsah a **viditelně se jmenuje "Moje docházka"** — vnitřní identifikátor zůstal `moje_dochazka_b`, přejmenoval se jen popisek dlaždice a nadpis obrazovky.

Zároveň byly **zrušeny čtyři dlaždice a jedna cesta na webovou stránku** v sekci DOCHÁZKA: Dnešek, Týden, Můj plán, Historie a stará "Moje docházka" (otevírala stránku `/moje-dochazka`). V sekci zůstaly tři dlaždice: Moje docházka, Moje absence, Požádat o opravu.

## Odkud obrazovka bere data

**Záměrně tentýž zdroj jako ERP přehled "Opravy docházky / Najít člověka"** (`fw.data_source` kód `dochazka.prehled_dnu_clovek`):

- řádky dnů: `tenant.att_day_summary` (proto jsou vidět i dny s čistou absencí, bez časů),
- hodiny: `tenant.att_den_hodiny(2, od, do)` → `hodiny_mzdove` + `hodiny_absence`,
- příchod/odchod: `min(started_at)` / `max(ended_at)` z `tenant.att_entry` bez `superseded` a bez typu `day_end`.

Nová funkce **`g2007.python` kód `att_moje_dny`** (jen ke čtení, `vedlejsi_ucinek=false`), adresa **GET `/app/dochazka/moje-dny?dni=N`** (tenká spojka v jádře, vzor delegáta jako `att_day_detail`). Jediný rozdíl proti ERP: místo působnosti editora (`att_fix_viditelni_emp`) vrací **výhradně vlastní `user_id`** přihlášeného. U lidí se dvěma docházkovými kartami se stejně jako v ERP bere jedna karta (`DISTINCT ON (user_id)`, aktivní přednostně), aby čísla v mobilu seděla s ERP.

Rozbalení dne používá **už existující** `/app/attendance/day-detail` (`att_day_detail`) — vrací i rozpad z `tenant.vyroba_work`. Nic v obrazovce nejde upravit ani smazat.

Přepínač období Týden / 14 dní / 30 dní / 90 dní / Rok (výchozí 30) posílá parametr `dni`; vzhled karet dne je převzatý ze stránky `moje-dochazka.html`.

**Dny bez hodin i bez časů se nevypisují** (rozhodl Jiří Honomichl) — seznam je o odpracovaných dnech a dnech s absencí.

## Co se přitom NEsmělo smazat (ověřeno v kódu)

- **Obrazovka `plan` zůstává.** Dlaždice Týden a Můj plán ji jen otevíraly; volají ji i `20_home_phone_notifs.js` a `35_apps_vedeni.js` (Aplikace → LIDÉ & DOCHÁZKA → Plán).
- **Šablona dne `_dnesScreen` zůstává** — používají ji `51_skupiny_sdileny.js` a `52_vyroba.js` pro pohled na kolegu.
- **`dochListLoad` a `_dochRail` zůstávají** — plní sekce na hlavní obrazovce docházky.
- Stránka `/moje-dochazka` existuje dál (žije v gitu), jen na ni nevede dlaždice.

## Pravdivost nápovědy

Ve stejném zápisu se opravilo **jedenáct míst**, která po zrušení dlaždic lhala: nápověda, tahák, mluvený průvodce i komentáře v kódu. Dvě z nich byla nepravda starší než tato změna — mluvený text tvrdil, že "Tady budu jinde" je dlaždice (tlačítkem je od 9. 9. 2026) a vyjmenovával obrazovku "Moje žádosti" (zrušena 8. 9. 2026).

**Funkce se zrušením Historie nezanikla, jen cesta:** tlačítka ⏱ Zkrátit konec / 🧾 Zakázka… / ✋ Nesedí… žijí na žluté kartě potvrzení dne pod "🔍 Raději chci vidět detaily…".

Fotky v mluveném průvodci byly téhož dne přefoceny (šest z devíti) postupem ze znalosti `doc-system-strategie-obrazky-navodu-dochazky-jak-poridit`; recept s přepsáním odpovědi serveru znovu potvrzen — pojistka nahlásila nula pokusů o zápis a v `tenant.att_entry` nevznikl žádný řádek.

