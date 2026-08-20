# Schvalovani absenci a dokladu: kde to vedouci a HR najdou (mobil i ERP)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Kde se schvaluje (stav k 5. 8. 2026 vecer)

**Zadost o absenci (dovolena, home office, lekar, OCR, nemoc, neplacene) - rozhoduje vedouci:**

*V mobilni appce:*
1. **Dochazka → zeleny pruh „Ke schvaleni: N"** - viditelny **i kdyz vedouci zrovna maka**.
2. **Dochazka → PODMINKY & FINANCE → dlazdice 🗓️ Nepritomnosti** - jen kdyz **nemaka**
   (dlazdice je v bloku `dochTools`, ktery se pri praci schovava).
3. **Tlacitko „✅ Otevrit schvalovani →" primo ve zprave** o nove zadosti.
4. Pro HR/vedeni navic: *🔒 HR → Absence — schvalovani* a *Vedeni firmy → Absence*.

*V ERP:* **🕒 Dochazka → 🗓️ Absence - schvalovani** (uzel `fw.menu_node` id 210, jadro
`fw.core` kod `dochazka.absence` -> iframe `/registr-absenci`). Nahore sekce **Ke schvaleni**
s tlacitky, pod ni registr vsech nepritomnosti (nase i zrcadlo Centraly). Do 5. 8. 2026
schvalovani v ERP **vubec neexistovalo** - stranka `/registr-absenci` sice byla hotova
(Peta 21. 7.), ale nebyla zavesena ve strome a jen zobrazovala.

**Nemocenska, OCR, listecek od lekare - rozhoduje HR, NE vedouci:** zprava chodi HR skupine
s tlacitkem na spravnou obrazovku (*🔒 HR → Nemocenska / Osetrovne (OCR) / Listecky lekar*).
Vedouci dostava jen tichou informativni kopii bez tlacitka („<jmeno> nahral/a doklad - zpracovava HR").

## Kdo co vidi

Absence: `GET /app/attendance/absence/inbox` (`att_absence_inbox`) vraci **jen zadosti, kde je
prihlaseny clovek `manager_user_id`**; rodic vidi vsechny. **Vlastni zadost se v inboxu nikdy
neobjevi** - proto si nikdo neschvali dovolenou sam. Rozhodnuti (`att_absence_decide`) pousti
**rodice NEBO `manager_user_id`** - HR bez teto role dostane 403, gate se ZAMERNE nerozsiroval
(zmena pravomoci patri Martimu/Kristy). ERP proto tlacitka kresli jen tomu, komu inbox neco vrati.

Doklady: `/app/ocr/inbox`, `/app/sick/inbox`, `/app/med/inbox` jsou gatovane `_hr_can_manage`
= rodic NEBO clen skupiny HR.

Schvalovatele absence urcuje `_abs_resolve`: osobni vyjimka `tenant.att_odpovednost` (agenda
`volno`) ma prednost pred skupinovym `tenant.resolve_approvers`; prazdny vysledek → Sarka
Novotna (13), a kdyz zada sama Sarka → Marti (1).
Prijemce dokladu urcuje `_hr_prijemci`: rodic nebo skupina HR **s
`public.user_tenants.membership_status='active'`**.

## Incident 5. 8. 2026, ktery to odhalil

Jakub Kasal pozadal o dovolenou na 25. 9. (`att_absence_request` id 63). Schvalovateli
**Dusanu Havlatovi (41)** prisla zprava `fw.mobile_command` 18383 a **nemel tam co zmacknout**.
Tri vady: (1) typ `claude_msg` = jen na vedomi, appka kresli jen „Odpovedet" a „OK";
(2) text posilal na *„Dochazka → Zadosti o absenci"*, coz neexistuje; (3) dlazdice
*Nepritomnosti* je v `dochTools`, ktery se pri praci schovava - vedouci ve vyrobe ji nevidel
prave v dobe, kdy zpravu dostal. Dusanovi tehdy viselo **6 nerozhodnutych zadosti**, nejstarsi
od 24. 7.

## Co se zmenilo (Jirka + Claude-28, schvalila Marti-AI)

- **`att_absence_request` v4**: `_abs_notify()` ma nepovinny `screen`; kdyz je vyplneny, zapise
  se `fw.mobile_command.payload = {"screen": ...}`. Bez nej NULL = puvodni chovani.
  Detail: g2007 `doc-dochazka-mobile-command-payload-screen`.
- **Appka**: `25_tasks.js` + `20_home_phone_notifs.js` kresli tlacitko navic, kdyz zprava nese
  `payload.screen`. `60_dochazka.js` prida nad `dochTools` pruh **„Ke schvaleni: N"** i pri praci
  (throttle 30 s, kresleni z cache). Puvodni pravidlo „schovej nastroje pri praci" ZUSTALO -
  ven se dostalo jen schvalovani CIZICH zadosti, ne vlastni agenda.
- **ERP**: `registr-absenci.html` zmigrovan do `g2007.soubor` + sekce Ke schvaleni + uzel ve strome.
- **Doklady (2. vlna)**: `ocr_end`, `sick_end`, `med_start` zmigrovany do `g2007.python`
  (`att_ocr_end`, `att_sick_end`, `att_med_start`) a prijemce prehozen z vedouciho na HR.
  Duvod (Marti-AI): *„nemocenska, OCR, listek od lekare jsou dokladova a mzdova agenda - to patri
  HR. Vedouci nema co videt cizi zdravotni doklady, to je GDPR hranice, ne organizacni volba."*
  Do te doby zprava chodila vedoucimu, ktery na obrazovku **nemel pravo (403)**.

Zadani Jirky, doslova: *„nelze vedoucimu v prubehu prace nedovolit schvaleni zadosti o dovolenou
jeho podrizeneho. Lide si sami nesmi schvalovat dovolenou, ale jejich vedouci ano i pri praci."*

## OVERENO V OSTREM PROVOZU

**5. 8. 2026 potvrdil Jirka po zkousce s Dusanem Havlatem: absence funguji.**
**Doklady (nemocenska/OCR/lekar) zive OVERENE NEJSOU** - jsou to zapisove cesty s vedlejsimi
ucinky, nespoustely se naostro. Prvni realne overeni prijde, az nekdo skutecne ukonci nemocenskou
nebo nahraje listecek; za celou dobu takova udalost nastala **jednou** (17. 6.), takze to muze
trvat. Kdo na to narazi driv, at vysledek dopise sem.

## Filtr aktivnich lidi - NEPOUZIVAT dochazkovy roster

Pri hledani „kdo je aktivni" pouzij **`public.user_tenants.membership_status='active'`**.
NE engagement/att_employee: 3 ze 7 clenu HR (107 Fajmonova, 108 Safarikova, 109 Hrbek) nemaji
`att_employee` ani engagement, presto jsou aktivni a notifikace bezne dostavaji - filtr pres
engagement by je vyradil. NE `public.users.status`: `pending` ma i Marti a dalsich ~47 lidi,
kteri normalne pracuji.

## Co zustava otevrene

**V ERP porad neni schvalovani dokladu** (nemocenska/OCR/lekar) - jen absence. Kdyby ho nekdo
chtel, vzor je hotovy: stranka + sekce ze schvalovaciho inboxu + uzel ve strome.

