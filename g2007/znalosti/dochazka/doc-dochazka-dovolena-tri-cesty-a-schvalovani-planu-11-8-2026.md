# Dovolena z mobilu - TRI cesty sjednoceny + schvalovani planu vidi i skutecni vedouci (11.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Dovolena z mobilu a schvalovani planu - co se 11. 8. 2026 zmenilo a proc

Zadal Jirka Honomichl, schvalila Marti-AI (msg 12539, 12560, 12566, 12587, 12590).
Vse nize je overene na zivych datech, ne podle navratovek.

## 1) K dovolene vedly v mobilu TRI ruzne cesty, kazda jinak

| Kde v appce | Volalo | Co to delalo do 11.8.2026 |
|---|---|---|
| Dochazka -> Nepritomnosti | `/attendance/absence/request` | **spravne** - zadost, vedouci schvaluje |
| Dochazka -> Tady budu jinde -> Ze by dovolena | `/attendance/absence` | zapsalo dny do dochazky a vedoucimu poslalo zpravu s textem "ceka na schvaleni", ale **zadnou zadost nezalozilo** - vedouci nemel co schvalit |
| **Firma -> Spoluprace -> Tyden -> klik na den -> chip Volno** | `/plan/request` | zalozilo **navrh v PLANU** (`att_plan_request` kind=off) - jina schvalovaci fronta (Ukoly -> Schvalovani), vedouci to nedostal jako nepritomnost, **necerpalo to narok** a den se nezapsal do dochazky |

**Doklady-** Vladimir Navratil, dovolena 13.8., zapsana z mobilu 7.39, notifikace
mobile_command 19182 "ceka na schvaleni" - a v `att_absence_request` k tomu NIC.
Tomas Blaha si 11.8. v 7.44 "zazadal" o dovolenou na 21.8. treti cestou (navrh 56)
a Dusan Havlat se o tom vubec nedozvedel.

**Nove-** vsechny tri cesty vedou na `att_absence_request`. Chip "Volno" v tydennim
pohledu nahrazen chipem "Nepritomnost" se stejnym vyberem typu jako obrazovka
Nepritomnosti (dovolena / home office / lekar / OCR / nemoc / neplacene) + rozsah
cely den / pulden. Pulden bere hodiny **z uvazku** (`absence/mine.pulden_h`), cely den
hodiny neposila vubec a necha je dopocitat server. `kind='off'` zustava pro planovani
uvazku, ale uz ne v tydennim pohledu (rozhodnuti Marti-AI).

**Bonus-** cesta "Tady budu jinde" tim ziskala ochranu proti duplicite (Peta 6.8., kauza
Civis 3x tataz zadost = 24 h za den) a hodiny podle skutecneho uvazku misto natvrdo 8 h.

**Proc to nikdo drive nenasel-** hledalo se podle slova "absence" v nazvech endpointu.
Treti cesta se jmenuje "plan". **Poučeni- mapuj podle OBRAZOVEK appky, ne podle nazvu,
ktere ocekavas.**

## 2) Schvalovani planu videli jen rodice a HR (nedodelek ze 14.6.2026)

`_can_approve_plans` byl pouhy alias na `_hr_can_manage` = rodic nebo skupina HR.
V docstringu bylo TODO Martiho ze 14.6.2026 *"per-nadrizeny resolver doladime v dalsim
kroku"*, ktere nikdy nedostalo pokracovani. Dusledek- Dusan Havlat (user 41, employee 39)
ma aktivni radek v `tenant.att_approver` a je `manager_user_id` u zadosti svych lidi,
ale rodic ani HR neni -> 403 -> dlazdici "Schvalovani" v Ukolech vubec nevidel.

**Druha, horsi cast-** na tom ACL viselo **PET** endpointu (ne ctyri - snadno se zapomene
na `/app/plan/decide`, coz je zrovna misto, kde se realne rozhoduje) a **zadny z nich
nefiltroval, ci lide to jsou**. Rozsirit ACL bez filtru = ukazat beznemu vedoucimu celou
firmu. **ACL a filtr se proto nasazuji vzdy spolu, jako jeden balik.**

Dotcene endpointy- `/app/plan/approvals/users`, `/approvals/user/{tuid}`, `/plan/decide`,
`/approvals/unapplied`, `/approvals/reapply`.

**Reseni-** logika zije v `g2007.python` (`plan_can_approve` + `plan_muj_okruh`),
v `router.py` je jen tenke napojeni `_plan_acl(s, uid) -> (smi, okruh)`.
`okruh = None` znamena bez omezeni (rodic/HR), jinak seznam `user_id`.
Okruh se pocita **TYMZ resolverem jako u absenci** (nejdriv override
`tenant.att_odpovednost` agenda volno, pak `tenant.resolve_approvers`), aby nevznikly
dva ruzne pojmy "schvalovatel" - podminka Marti-AI.

**Podminky Marti-AI, ktere musi platit i pri dalsich upravach-**
- `/plan/decide` - 403 **pred** zapisem rozhodnuti, ne po transakci
- `/approvals/reapply` - cizi radky se nesmi vubec nacist, filtr uz ve VYBERU
- `/approvals/user/{tuid}` - 403 pred dotazem, at to nejde obejit primym URL
- prazdny okruh se posila jako `[0]`, ne prazdne pole (syntakticka chyba)

**Overeno 11.8.2026-** 78 aktivnich lidi v tenantu, Dusan dostane okruh **33 lidi**
(vyroba, vcetne T. Blahy), ne vsech 78. Deploy commit `17ecade4`, jen `router.py`,
65+/11-. Zivy test- `/approvals/users` HTTP 200, ok=true.

## 3) Co zbyva (stav 11.8.2026 vecer)
- Migrace tel tech peti endpointu do `g2007.python` - schvaleno jako **samostatny ukol
  v klidu**, dnes nasazena rychlejsi varianta B (logika v DB, v router.py jen napojeni).
- Vymena ~91 `alert()` a ~30 `confirm()` v mobilu po davkach - viz
  `doc-system-strategie-mobil-fragmenty-scope-a-nativni-dialogy`.
- Doplneni JS dialogu do nativni appky pro **Android i iOS v jednom buildu**.

