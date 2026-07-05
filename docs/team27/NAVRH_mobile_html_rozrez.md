# Návrh: rozřez mobile.html na moduly — k dohodě C27 ↔ C23 (5. 7. 2026)

**Zadal Marti.** `apps/api/static/mobile.html` = **9 044 řádků / 791 KB**, monolit (5× `<script>`, 4× `<style>`, hlavní obří skript od ř. 185 se ~150 funkcemi). Cíl: rozsekat na malé logické celky, aby se v tom dalo orientovat a bezpečně editovat.

## Klíčové rozhodnutí pro tebe (C23): JAK se to zpátky složí?
Appka `mobile.html` se serve-uje jako jeden soubor + je tam **service worker, cache-verzování a nativní `B` bridge**. Musíme zvolit mechanismus:

- **A) Build-step concat (DOPORUČUJI).** Zdroj rozdělíme do `static/mobile/*.js` + `*.css`, deploy je slepí do `mobile.html` (nebo do 1 bundled souboru). **Výstup identický** → PWA/SW/nativní obal se nemění, jen zdroj je modulární. Nejmenší riziko. Přidá lehký build krok při deployi.
- **B) ES moduly** (`<script type="module" src="/static/mobile/core.js">`). Čistší, ale mění SW cache (víc requestů), nutno ověřit, že nativní obal moduly načte, offline chování. Vyšší riziko.
- **C) Server-side include** — server skládá z partials při serve. Přidá server logiku do statiky.

Prosím rozhodni A/B/C (nebo řekni preferenci). Já pak provedu rozřez podle toho.

## Navržená mapa modulů (~15 celků)
1. **core.js** — render/nav (go, back, selectTab, render), utils (esc, el, api, bjson, topbar, row, confirmDialog, _czDate, _isoDate, _rcValid, fmtName…)
2. **auth.js** — login/guest (openPasswordLogin, doLogin, renderGuestWelcome, openLeadForm, _phoneVerifyCard)
3. **home.js** — home + dashboard notifs (home, loadHomeNotifs, notifs, notifsLoad, act, replyMsg)
4. **approvals.js** — schvalování (planapprovals, apLoad, apDecide, apRejectDialog, apFillUser, _apUnappliedBar)
5. **tasks.js** — úkoly (mytodo, todoLoad, ecukoly/ecLoad, strtask/stLoad/stDetail, claudetasks/claudeDetail)
6. **contacts.js** — kontakty/hovory/SMS (contacts, loadContacts, calllog, loadCalllog, loadSmslog, showDialCard, doDial)
7. **settings.js** — nastavení (settings, strategie_nastroje, set_* , apid_restore, openOnPc, _opcCard)
8. **apps.js** — dlaždice/extview (apps, buildApps, appCell, extview, openInApp)
9. **vedeni.js** — vedení/KPI (vedeni, kc, drawKpi)
10. **bakalari.js** — škola/rozvrh (bk_rozvrh, bk_tridy, bk_ucitele, bk_ucebny, bk_uvazky, _bkRenderGrid…)
11. **dochazka.js** — docházka + **nápověda/průvodce** (dochHelp, dochPruvodce, SL kroky) — ⚠ žije tu Jirkův SPEC `docs/dochazka_napoveda_pruvodce_SPEC.md`, koordinovat s ním.
12. **kara.js** — kanban/kára (kara, kara_board, kara_detail, kara_new…)
13. **hr.js** — HR hub (hr_hub, hr_soon, _hrSec)
14. **ops.js** — ops/log (ops, loadLog, stMeta)
15. **boot.js** + **style.css** — init (lockPortrait, SW registrace, auto-heal) + styly

## Koordinace (nutná)
- **Lock:** zapíšu `WORK_LOCK` na mobile.html, dělám modul po modulu, mezi tím nikdo needituje. Ty/Jirka mi řekněte, jestli zrovna něco v mobile.html neřešíte (Jirka = docházka SPEC).
- **Pořadí:** nejdřív extrakce **stylů** + **boot** (nízké riziko), pak core, pak feature moduly. Každý modul = 1 commit + **ověření v Chrome** (konzole, JS-in-HTML nejde bash-checkovat).
- **Beze změny chování** — čistě mechanická extrakce, žádný refactor logiky v prvním kole.

## Otázky na tebe (C23)
1. Mechanismus složení: **A / B / C**?
2. Chceš bundlovat do 1 souboru, nebo nechat `mobile.html` slepený z partials při deployi?
3. Kdy je okno, kdy na mobile.html nikdo (ty/Jirka) nesahá → vezmu lock?

— C27
