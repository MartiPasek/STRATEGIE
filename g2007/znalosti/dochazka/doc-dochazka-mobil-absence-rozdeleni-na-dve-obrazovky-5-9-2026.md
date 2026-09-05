# Mobil: obrazovka Absence rozdelena na dve - "Moje absence" a "Ke schvaleni" (5. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobil: jedna obrazovka Absence rozdelena na dve (5. 9. 2026)

**Zadal Jiri Honomichl, provedl Claude-28, schvalila Marti-AI (msg 14432, 14438, 14448).**
Vzniklo z auditu duplicitnich cest `doc-system-strategie-mobil-duplicitni-cesty-audit-5-9-2026`.

## Co bylo pred tim

JEDNA obrazovka `absence`, ktera se prepinala podle role. Kdo byl schvalovatel, tomu se
schoval formular vlastni zadosti a misto nej dostal "ukazatel cesty" zpatky do Dochazky.
Ten ukazatel byl **obchvat** kolem toho, ze se dve role tlacily na jedne obrazovce -
rozdelenim ZANIKL.

## Jak to je ted

| obrazovka | kod | vede sem | co je na ni |
|---|---|---|---|
| Moje absence | `moje_absence` (NOVA) | Dochazka -> Nepritomnosti | formular Nova zadost (nove I PRO SCHVALOVATELE), Moje zadosti + stav + Zrusit, hlaska bez karty |
| Ke schvaleni | `absence` (puvodni) | Dochazka -> Ke schvaleni | cizi zadosti k rozhodnuti + NOVE historie vlastnich rozhodnuti |

**Jine cesty NEEXISTUJI.** Zrusily se tri starsi vstupy: Vedeni -> Absence,
HR -> "Absence - schvalovani" a mrtvy radek "Absence - zadosti a schvalovani"
(ten lezel za nedosazitelnou obrazovkou `hr`).

## ⭐ PROC si schvalovani nechalo nazev `absence`

**Stare notifikace, ktere lidem uz lezi v telefonu, nesou `screen="absence"` a text
"Otevrit schvalovani".** Kdyby se nazvy prohodily, posilaly by schvalovatele na obrazovku
vlastnich zadosti a **zpetne to opravit nejde**. Pet z sesti tehdejsich vstupu navic
fakticky znamenalo schvalovani. Potvrdila Marti-AI.

## Kde to vsechno zije (7 dilku + 2 skripty + jadro)

Obrazovka NENI v `60_dochazka.js`, jak by se cekalo - je v **`50_skupiny_vyroba.js`**.
Pridani nove obrazovky do mobilu vyzaduje **ctyri** mista, ne jedno:
1. `10_core.js` - stub `window.__M2W.<nazev> = mkWrap();`
2. dilek s definici - funkce + `window.__M2W.<nazev>.__setImpl(<nazev>);`
3. `72_migrace_sw_isds.js` - promenna v hlavicce dalsiho bloku (`var absence=window.__M2W.absence, ...`)
4. `73_pref_poptavka.js` - klic v `var SCREENS={...}`
Bez kteregokoli z nich obrazovka tise neexistuje. Popisky tlacitek notifikaci maji
zalozni mapu jeste v `20_home_phone_notifs.js` a `25_tasks.js`.

## Notifikace vedou kazda jinam (zadal Jirka 5. 9. 2026)

- "nekdo te zada o schvaleni" (`att_absence_request`) -> `screen="absence"` = Ke schvaleni. Bylo uz driv.
- "vedouci rozhodl o tve zadosti" (`att_absence_decide`, v16 -> **v17**) -> nove
  `screen="moje_absence"`, popisek "🗓️ Otevrit moje absence →". **Do 5. 9. tahle zprava
  nemela zadne tlacitko vubec** - lokalni `_abs_notify` v te funkci ho neumela prilozit
  (mela kratsi hlavicku nez tataz funkce v `att_absence_request`). Zaloha puvodni verze:
  `att_absence_decide__zaloha_20260905`.

## Historie schvalovani

Novy zdroj **`att_absence_decided`** (`GET /app/attendance/absence/decided?limit=&offset=`),
tenka spojka v `router.py` (commit `62c70440`). Cte `tenant.att_absence_request`
(`decided_by_user_id`, `decided_at`). Strankovane od zacatku na doporuceni Marti-AI.
Historii vidi jen schvalovatel; kdo jim neni, dostane prazdny seznam, ne chybu.

## Technicky dluh (vedomy, schvalila Marti-AI)

Obe obrazovky maji **vlastni kopii** pomocniku `chip`/`cz` a ciselniku typu absence -
dilky mobilu nesdileji scope. **Kdyz se meni jeden, musi se i druhy.**

## Kdo je "schvalovatel"

16 lidi k 5. 9. 2026, definice je `_je_schvalovatel` = osobni vyjimka v
`tenant.att_odpovednost` (agenda 'volno') NEBO aktivni radek v `tenant.att_approver`.
Rodice v tom zamerne nejsou (viz `doc-dochazka-vedouci-jeden-zpusob-a-fronta-rodicu`).
`att_absence_decided` drzi tuto definici 1:1 - kdyz se meni, meni se na obou mistech.

