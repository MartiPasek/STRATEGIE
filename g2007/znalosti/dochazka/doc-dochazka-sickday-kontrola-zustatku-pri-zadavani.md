# Sick day a dovolená v mobilu: kontrola zůstatku už při zadávání (27. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Sick day a dovolená v mobilu — kontrola zůstatku už PŘI zadávání

**27. 8. 2026.** Zadal Jirka Honomichl, schválila Marti-AI (msg 13853 + 13856).
Podklad: mail Peti Šafránkové z 26. 8. 2026, její tři body k sick day.

## Co bylo špatně

Obrazovky pro zadání absence v mobilu **neznaly zbývající nárok**. Člověk si mohl vyklikat
6 h sick day, i když mu zbývaly 2 — a teprve **po odeslání** se dozvěděl, že se zapsalo míň.
U dovolené neexistoval strop vůbec. Peťa 26. 8. 2026: *„nedovolit zadat víc, než jim zbývá."*

## Co bylo hotové UŽ PŘED zásahem (nedělej to znovu)

Z Petiných tří bodů byly **dva už splněné** a nesahalo se na ně:

1. **„Sick day se normálně zapisuje, nic se tiše nezahazuje"** — při částečném nároku se
   zapíše, co se vejde, a člověk dostane hlášku i notifikaci (`att_absence`).
2. **„Při nulovém nároku rovnou říct nemáš nárok"** — server vrací `ok=false` s vysvětlením
   a nabídkou přepnout na lékaře; mobil to zobrazí (ověřeno na živé verzi).

**Kdo bude opravovat „falešné hotovo", ať si nejdřív ověří, co server doopravdy vrací.**

## Co se změnilo — TŘI místa v mobilu

Dílek `apps/api/static/mobile_parts/60_dochazka.js` (v20 → v22), publikováno do
`apps/api/static_db/mobile.html` (v70 → v72). **Server se kvůli stropům NEMĚNIL** — jeho
pravidlo zůstává jako druhá pojistka.

| místo | jednotka | co dělá |
|---|---|---|
| sick day po hodinách | hodiny | tlačítka nad zůstatek zašednou, u vlastního počtu hláška hned při psaní |
| sick day na víc dnů (od–do) | hodiny | pracovní dny × denní fond proti zůstatku |
| **dovolená (od–do)** | **dny** | pracovní dny proti zůstatku ve dnech |

- Zůstatek se bere z `/api/v1/erp/app/dochazka/muj-prehled` — **tentýž zdroj jako obrazovka
  Můj přehled**, takže je to totéž číslo, jaké vidí personalistka v Nároku a čerpání.
- **Pozor na jednotky:** sick day je v HODINÁCH, dovolená ve DNECH. Nemíchat.
- Sdílený pomocník **`_pracDnu(od, dd)`** počítá **jen pondělí až pátek**, stejně jako server
  (`day.weekday() < 5` v `att_absence`). Jeden výpočet pro obě místa.

### Pozor: `chipsIn` se u sick day už nepoužívá

Sdílená funkce `chipsIn` neumí vrátit vytvořená tlačítka, takže by je nešlo zašednout.
Sick day si proto **staví vlastní tlačítka**. `chipsIn` zůstává beze změny pro ostatní
obrazovky — **nesahat na ni**, změna by měla neviditelný dopad jinde.

## Když se zůstatek nepodaří zjistit

**Záměrně se NEBLOKUJE nic.** Ukáže se věta, že zůstatek nešel zjistit, a zápis projde
na server, který rozhodne. Bránit člověku v zápisu kvůli výpadku spojení by bylo horší.

## Hláška „Zapsali jsme ti o X míň" (server, `att_absence` v21)

Opraveny tři věci najednou:

1. **Chyba ve výpisu:** stálo tam `"o " + _hh(_kr) + " min"`, jenže `_hh()` už samo připojí
   `" h"` — lidem se zobrazovalo **„Zapsali jsme o 2 h min"**.
2. **⚠️ Důvod se ROZLIŠUJE, protože příčiny jsou dvě.** `_kr` (zkráceno) vzniká
   ze dvou různých míst v `sickday_lekar_apply`:
   - `sickday` → zkrátil **zůstatek nároku** (`draw = min(požadavek, zbývá)`)
   - `medical` → zkrátil **strop 4 h na jednu návštěvu** (`hcap`); s nárokem to nesouvisí,
     co se do nároku nevejde, zůstane zapsané jako lékař a do `_kr` se to nepřičítá.

   **Napsat u lékaře „nemáš nárok" by byla nepravda.** Do 27. 8. tam byla jedna mlhavá věta
   („víc už pravidlo nebo tvůj zbývající nárok nedovolí"), ze které se nedalo poznat nic.
3. **Diakritika** — celý blok hlášek pro člověka byl bez ní („nez jsi chtel(a)").

## Jak to bylo ověřeno

Ne proklikáním v telefonu, ale takto (jde to zopakovat):

1. Živá stránka stažena přes `/mobile` — ne z kopie na disku.
2. Zaplaty aplikovány **nanečisto lokálně** a celá stránka zkontrolována na syntaxi
   (`node --check`) **PŘED** odesláním; přírůstek znaků seděl na znak.
3. Z živé stránky vyříznut blok a spuštěn v Node s náhradou prohlížeče a podvrženou
   odpovědí serveru:
   - **zbývají 3 h** → aktivní jen „2 h" a „3 h"; klik na „6 h" i po ručním obejití
     zašednutí neodešle nic; vlastní 5 h zašedne tlačítko a ukáže hlášku; 2 h projdou.
   - **zbývá 0 h** → zašedlé všechno.
   - **sick day od–do**, zbývá 16 h: po–út (16 h) projde, po–st (24 h) **neodešle nic**.
   - **dovolená**, zbývají 2 dny: po–út projde, po–st **neodešle nic**; při 0 dnech neprojde nic.
   - **server neodpověděl** → neblokuje se nic.
4. Počítání pracovních dnů ověřeno zvlášť: po–pá = 5, pá–po = 2, so–ne = 0.

## Souvislosti

- [[doc-dochazka-mobil-nemoc-ocr-lekar-jen-info-vedoucimu]] — nemoc, OČR a lékař z mobilu
- [[doc-system-strategie-editace-fragmentu-mobilu-pres-most-bez-primeho-zapisu]] — jak se dílek mění
- [[doc-system-strategie-spoustec-hlidacich-pravidel-pojistka]] — proč se na pojistku
  v `tenant.pojistka` (zatím) nedá spolehnout

