# Agendy (skupiny) — zdroj je tenant.staff_group pro ERP i mobil, nadrazéné složky nejsou agendy a kategorie Výroba/Kancelář není zařazení (8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

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

`gid=0` („Všichni“) je jiný — sloučí lidi ze **všech** agend **plus** aktivní docházkový
roster `tenant.att_employee`, aby nikdo nevypadl, když není v žádné agendě.

## ⚠️ TŘI NADRAZÉNÉ SLOŽKY NEJSOU AGENDY

`KANCELÁŘE` (id 14), `VÝROBA` (id 15) a `EXTERNÍ` (id 13) vznikly 24. 7. 2026 jako
**zastřešení** — ostatní skupiny na ně ukazují přes `parent_id`. **Nemají žádné vlastní
členy a mít je nemají.** Kdo je spočítá mezi agendy, dostane falešný nález „agenda bez lidí“.

Rozdělení k 8. 9. 2026: pod `KANCELÁŘE` → Vedení, IT, Nákup, VP, Obchod, E-plan, HR,
Finance, Úklid, PLC – koordinace · pod `VÝROBA` → Výroba, Zkušebna · pod `EXTERNÍ` → PLC ·
bez složky → DOCHÁZKA - OPRAVY, DOCHÁZKA - SCHVALOVÁNÍ VŠECH.

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

## Kde se agenda člověku přiřadí

- **Při náboru** — formulář „Přidat zaměstnance“ v kartě zaměstnance, políčko
  „Skupiny (docházkové / organizační)“. Je to **jediné místo v ERP**, které zapisuje
  do `staff_group_member`.
- **Dodatečně jen v mobilní aplikaci** — `/app/skupiny/<gid>/clen`. **V ERP dodatečně
  zařadit ani odebrat nejde**; dlaždice „Skupiny a kvalifikace“ v kartě je pouze ke čtení
  (tak ji Šárka zadala 21. 7. 2026).
- Kdo může zakládat a archivovat samotné agendy:
  [[doc-system-strategie-sprava-skupin-staff-group-jen-v-mobilu]].

**Důsledek, se kterým počítej:** lidi převedené ze staré Centrály (kartě vznikla dřív než
náborový formulář, tedy před 24. 7. 2026) **nikdo do agend nezapsal**. K 8. 9. 2026 bylo
bez agendy 7 lidí; šest z nich Jirka řešit nechce, zařazen byl jen Marek Horník (do Výroby).

## Kdo agendy a lidi v nich vidí

**Všichni, kdo mají appku** — seznam agend ani lidé v nich nejsou nijak omezené právy
(v kódu je to i napsané: „zatím vidí všichni vše“, Marti 10. 6. 2026).

