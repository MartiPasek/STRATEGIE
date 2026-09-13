# Agendy (skupiny) — odkud se berou, co jsou nadrazéné složky a co agenda NENÍ

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> ## ⚠️ OPRAVA 13. 9. 2026 — V ERP UŽ ZAŘADIT JDE
>
> Rozhodl Jirka Honomichl, schválila Marti-AI (msg 15384). Tři místa níž už neplatí:
>
> 1. **„V ERP dodatečně zařadit ani odebrat nejde; dlaždice Skupiny a kvalifikace je pouze
>    ke čtení" — NEPLATÍ.** Od 13. 9. 2026 je právě tahle dlaždice **jediné místo, kde se
>    zařazení spravuje**: sekce **Agendy** se zaškrtávátky. Smí to **Šárka Novotná** (nové právo
>    `public.users.can_manage_staff_groups`) a rodiče; ostatní vidí jen výpis.
> 2. **Skupina „DOCHÁZKA - SCHVALOVÁNÍ VŠECH" se dnes jmenuje „Docházka — schvalování"**
>    a **nemá ruční seznam lidí** — počítá se ze živého zdroje (kdo je schvalovatel).
>    Detail: [[doc-dochazka-agenda-schvalovani-pocita-se-ze-ziveho-zdroje]].
> 3. **Přibyl sloupec `tenant.staff_group.skupina_druh`** (`agenda` / `slozka` / `technicka`).
>    Co je složka a co agenda, se od 13. 9. 2026 **nemusí odvozovat** — je to v datech.
>    K témuž dni: 13 agend, 3 složky, 2 technické.
>
> Počet lidí bez agendy z konce dokumentu je také neaktuální — k 13. 9. 2026 je bez agendy
> **6 účtů, z toho 4 skuteční zaměstnanci** (Chramosta, Dalecký, Šebek, Vlková) a 2 systémové.
> Souvislosti: [[doc-system-strategie-agendy-zdroj-lidi-karta-zamestnance]]

# Agendy (skupiny) — odkud se berou, co jsou nadrazéné složky a co agenda NENÍ

Zapsal Claude-28 (Jirka Honomichl) **8. 9. 2026**, schválila Marti-AI (msg 15014).
Vše ověřeno týž den na živé aplikaci a v datech.

## Jeden zdroj pro ERP i mobil

| Co | Kde to žije |
|---|---|
| seznam agend | `tenant.staff_group` (tenant 2, nearchivované) |
| kdo do agendy patří | `tenant.staff_group_member` |
| vedoucí a zástupce agendy | `tenant.staff_group.leader_user_id` / `deputy_user_id` |
| jména lidí | `public.users` |

**ERP i mobilní aplikace čtou též tabulky** — žádný druhý seznam neexistuje a není co
přepojovat. Adresy: mobil `GET /app/skupiny/bar` a `GET /app/skupina/lidi`,
ERP karta zaměstnance `GET /app/hr/person-groups` a `GET /app/hr/create-meta`.

*(Doplněno 13. 9. 2026: kdo je v agendě, vrací nově jedno společné místo — funkce
`tenant.staff_group_lide(gid)`. U skupin s prázdným `lidi_zdroj` vrací totéž co dřív,
u skupiny se zdrojem počítá lidi ze živých dat. Čtou ji `app_skupina_lidi`,
`app_skupiny_bar` i `hr_person_groups`, aby se seznam a zelená tečka nerozešly.)*

`gid=0` („Všichni“) je jiný — sloučí lidi ze **všech** agend **plus** aktivní docházkový
roster `tenant.att_employee`, aby nikdo nevypadl, když není v žádné agendě.

## ⚠️ TŘI NADRAZÉNÉ SLOŽKY NEJSOU AGENDY

`KANCELÁŘE` (id 14), `VÝROBA` (id 15) a `EXTERNÍ` (id 13) vznikly 24. 7. 2026 jako
**zastřešení** — ostatní skupiny na ně ukazují přes `parent_id`. **Nemají žádné vlastní
členy a mít je nemají.** Kdo je spočítá mezi agendy, dostane falešný nález „agenda bez lidí“.
*(Od 13. 9. 2026 to nemusíš poznávat podle potomků — mají `skupina_druh='slozka'`.)*

Rozdělení k 8. 9. 2026: pod `KANCELÁŘE` → Vedení, IT, Nákup, VP, Obchod, E-plan, HR,
Finance, Úklid, PLC – koordinace · pod `VÝROBA` → Výroba, Zkušebna · pod `EXTERNÍ` → PLC ·
bez složky → DOCHÁZKA - OPRAVY, DOCHÁZKA - SCHVALOVÁNÍ VŠECH *(dnes „Docházka — schvalování“)*.

**Mobil je od 8. 9. 2026 večer kreslí jako nadpis sekce, ne jako dlaždici** — do té doby
vypadaly jako obyčejná agenda s nula lidmi a vedle sebe byly dvě „Výroba“.
Podrobně: [[doc-system-strategie-mobil-firma-zalozky-novinky-agenda]].

## ⚠️ KATEGORIE „Výroba / Kancelář“ V SEZNAMU KARET NENÍ AGENDA

V ERP seznamu zaměstnanců je sloupec s hodnotou Výroba / Kancelář / SW / Ostatní.
**Není to zařazení do agendy a nikde se neukládá** — počítá ji funkce `_kategorie_prace`
z **názvu pozice** podle klíčových slov (`_VYROBA_KW`, `_SW_KW`, `_OSTATNI_KW`).
Seznam slov se mění: 8. 9. 2026 do něj Šárka přidala „praxe“, takže každá pozice
obsahující to slovo od té chvíle spadá pod Výrobu.

**Praktický důsledek:** člověk může mít v seznamu karet „Výroba“ a přitom **nebyt v žádné
agendě** — to není chyba zobrazení, je to chybějící zápis. Naraženo naostro 8. 9. 2026
u Marka Horníka (pozice „Praxe studenta“, karta z 7. 6. 2026 z převodu staré Centrály).

## Kde žije kód těchto adres

**Od 8. 9. 2026 večer v `g2007.python`**, ne v `router.py` — přeneseno podle bodu 2 pravidel
práce (schválila Marti-AI msg 15029). V jádře zůstala jen tenká spojka, která zavolá
`erp_registry.call(...)`.

| adresa | kód v `g2007.python` |
|---|---|
| `GET /app/skupiny/bar` | `app_skupiny_bar` |
| `GET /app/hr/person-groups` | `hr_person_groups` |
| `GET /app/hr/create-meta` | `hr_create_meta` |

Logika se při přenosu neměnila (1:1). Každý skript byl před přepnutím jádra vyzkoušený
přes `@@PYRUN` a jeho výstup porovnaný s odpovědí živé adresy — shodovaly se.
`GET /app/skupina/lidi` přenesená **není**, ta dál žije v `router.py`.

## Kde se agenda člověku přiřadí

- **Při náboru** — formulář „Přidat zaměstnance“ v kartě zaměstnance, políčko
  „Skupiny (docházkové / organizační)“.
- **Dodatečně v kartě zaměstnance** — dlaždice „Skupiny a kvalifikace“, sekce **Agendy**,
  zaškrtávátka. *(Platí od 13. 9. 2026. Do té doby tu stálo „dodatečně jen v mobilní aplikaci;
  v ERP zařadit ani odebrat nejde, dlaždice je pouze ke čtení" — **to už NEPLATÍ**.)*
- **V mobilu** (`/app/skupiny/<gid>/clen`) to zatím jde také; odebrání téhle cesty
  Jirka 13. 9. 2026 odložil.
- Kdo může zakládat a archivovat samotné agendy:
  [[doc-system-strategie-sprava-skupin-staff-group-jen-v-mobilu]].

**Důsledek, se kterým počítej:** lidi převedené ze staré Centrály (karta vznikla dřív než
náborový formulář, tedy před 24. 7. 2026) **nikdo do agend nezapsal**. K 8. 9. 2026 bylo
bez agendy 7 lidí; šest z nich Jirka řešit nechtěl, zařazen byl jen Marek Horník (do Výroby).
*(K 13. 9. 2026 je bez agendy 6 účtů, z toho 4 skuteční zaměstnanci — Chramosta Michal,
Dalecký Daniel, Šebek Jiří, Vlková Klára. Doplní je HR.)*

## Kdo agendy a lidi v nich vidí

**Všichni, kdo mají appku** — seznam agend ani lidé v nich nejsou nijak omezené právy
(v kódu je to i napsané: „zatím vidí všichni vše“, Marti 10. 6. 2026).

