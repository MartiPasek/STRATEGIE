# Dušan — ERP přístup „least-privilege" + soudeček Výroba (BUILD PLÁN)

## ✅ HOTOVO 8.7.2026 (LIVE, ověřeno)
- Kód: `_ERP_SCOPED_USERS={41}` gate + whitelist strom + **rodičovský bypass** (rodič vidí i
  private uzly) — commity f8413d8e + 99225db0.
- DB: view `tenant.vyroba_dusan_team` (36 lidí, rekurzivní post 24) + kořen „🏭 Výroba" (id 165,
  private, uids={41}) + 5 přehledů (cores 172–176), banner #1067 + #1068.
- Ověřeno: Dušan (scoped) vidí PŘESNĚ 6 uzlů (Výroba + 5 přehledů), nic víc. Filtr týmu vrací
  data (20 859 záznamů docházky, 36 zaměstnanců). Rodiče vidí Výroba taky; ostatní členové ne.
- **8.7. dodáno:** admin bypass (is_parent_or_admin, aby Jirka/admin viděl Výroba) — deploy
  b885df38. + 3 další přehledy (bannery #1069/#1070): Kdo kde dnes, Organizační struktura,
  Pracovní režim — kopie přes `replace()` z originálů + filtr týmu (view `tenant.vyroba_dusan_posts`
  pro org podstrom). Pozor: work_params replace nesedl (whitespace) → opraveno wrapem `SELECT *
  FROM (...) w WHERE w.id IN (att_employee týmu)`; ověřeno 36 (tým) vs 85 (všichni).
- **8.7. dodáno #2 (banner #1071):** Typy záznamu + podsoudeček „🏭 Plánování výroby" (Plán
  výroby + Týdenní plán, filtr `vp.user_id IN tým`). Výroba má teď **9 přehledů + folder Plánování**.
- **Pokrytí Docházky (11 přehledů):** 9 zkopírováno do Výroby. NEzkopírováno: **Finance lidí**
  (= mzdy, `mzda_mes_plan`) a **Benefity** — Martinova hranice (Dušan NEsmí do mezd). Výkonnostní
  finance = NOVÝ přehled z výrobních dat (`vyroba_plan` zakázky/hodiny), ne kopie mzdové Finance lidí.
- **Follow-up:** (a) PWA install u Dušana + ověřit login (účet pending); (b) volitelně Typy
  záznamu (číselník); (c) výkonnostní finance (zakázky/hodiny/efektivita bez mezd) = zvlášť.


> Připravil Claude-28 (Jirka), 7.–8. 7. 2026. **STATUS 8.7.: Marti Pašek dal Jirkovi souhlas
> se do toho pustit (napřímo). Jde se stavět po finálním OK Marti-AI.** Přístup PER-UŽIVATEL
> (přes jméno, jako Eliška/Pavel), NE nová role. Dušan zůstává role `employee` + scoped allow-list.
> **Finance lidí + Benefity: v PRVNÍM buildu NEJSOU** (Martinova hranice z msg 10579 — Dušan
> NEvidí mzdy/výplatní pásku/faktury). Výkonnostní „finance ve výrobním smyslu" (zakázky/
> hodiny/efektivita) = samostatný FOLLOW-UP přehled, ne kopie mzdové Finance lidí.

## Cíl
Dušan Havlát (user 41, vedoucí výroby) uvidí v ERP (PWA na PC) **jen soudeček „🏭 Výroba"**
s přehledy **jen o svých podřízených**. Originály v Docházce se NESAHAJÍ — děláme KOPIE
řetězce a do jejich SQL přidáme filtr na tým. Nic víc (žádné CRM/faktury/finance firmy).

## Finální rozhodnutí (8.7.)
1. Podřízení = **org struktura** (post „Vedoucí výroby" 24), ne výrobní plán. Zahrnuje i
   **Přípravu výroby** (post 26) — je pod postem 24, takže v týmu už JE.
2. **Finance lidí + Benefity → NEJSOU v prvním buildu.** Marti (msg 10579): Dušan „rozhodně
   nemá vidět do mezd a do faktur". Mzdový přehled „Finance lidí" ani „Benefity" mu tedy
   nedáváme. Výkonnostní finance (zakázky/hodiny/efektivita, BEZ mzdových složek) = samostatný
   follow-up přehled k pozdějšímu návrhu.
3. **Přístup = per-uživatel (přes jméno)**, ne role. Dušan zůstává `employee` + scoped allow-list.
4. UI-scoping teď OK; tvrdá datová zeď (per-node ACL) = Fáze 2.

## Tým = podřízení postu „Vedoucí výroby" (post_id 24)
Rekurzivní potomci postu 24 → 35 lidí (bez Dušana). **Pozor (data-quality):** org mixuje
reportovací a kvalifikační posty (VAZAČ-JEŘÁBNÍK / ZÁMEČNÍK visí pod 24 a nabírají ~celou
výrobní podlahu vč. Dušana). Pro MVP = přijatelné (jsou to jeho výrobní lidé). Filtr držíme
DYNAMICKY jako subquery (zůstane aktuální):

```sql
-- KANONICKÝ filtr týmu (vlož do WHERE kopií jako: AND <clovek>.user_id IN ( ... ))
WITH RECURSIVE tree AS (
  SELECT id FROM tenant.org_post WHERE id = 24
  UNION
  SELECT p.id FROM tenant.org_post p JOIN tree t ON p.parent_post_id = t.id WHERE p.aktivni
)
SELECT ae.user_id
  FROM tenant.org_post_assign ca
  JOIN tenant.att_employee ae ON ae.id = ca.employee_id AND ae.tenant_id = 2
 WHERE ca.post_id IN (SELECT id FROM tree) AND ca.aktivni
   AND COALESCE(ca.zastupce_role,0) = 0 AND ae.user_id IS NOT NULL
```

## Mechanika přehledů (zjištěno)
Každý přehled = řetězec: `fw.menu_node → fw.core → fw.data_source → fw.data_set (sql_text) →
fw.data_source_op (select/default) → fw.comp_def (grid type_id=306, root=1)`.
**SQL žije v `fw.data_set.sql_text`**, db_connection_id=1 (PostgreSQL data_db).
Kopie = ten samý řetězec s NOVÝMI kódy (`vyroba.dusan_*`) + do sql_text přidán filtr týmu.

## Přehledy do soudečku Výroba (KOPIE)
| Přehled (originál) | core | zdroj. data_set (sql_text) | filtr týmu |
|---|---|---|---|
| Kdo je v budově / Kdo je kde? | 107 | `system_new.hr_presence_board_list` | `p.user_id IN (tým)` |
| Kdo kde dnes | 114 | `system_new.hr_kdo_kde_dnes*` (pull z DB) | dle sloupce user_id |
| Záznamy docházky | 109 | `system_new.hr_att_entries_list` | `em.user_id IN (tým)` |
| Měsíční přehled | 110 | `system_new.hr_att_monthly_list` | `em.user_id IN (tým)` |
| Zaměstnanci | 111 | `system_new.hr_att_employees_list` | `user_id IN (tým)` |
| Měsíční zůstatky | 113 | `system_new.hr_att_balances_list` | `em.user_id IN (tým)` |
| Organizační struktura | 115 | `system_new.hr_org_struktura*` (pull) | Dušanův podstrom |
| Pracovní režim | 123 | `system_new.hr_work_params*` (pull) | dle user_id |
| Typy záznamu (číselník) | 112 | `system_new.hr_att_types_list` | bez filtru (číselník) — volitelně |
| ~~Finance lidí (mzdy)~~ | 116 | — | **NENÍ v buildu** (Martinova hranice — mzdy ne) |
| ~~Benefity~~ | 120 | — | **NENÍ v buildu** (osobní odměna — ne) |

Pozn.: Finance lidí (116) + Benefity (120) do Dušanovy Výroby NEDÁVÁME. Výkonnostní finance
(zakázky/hodiny/efektivita bez mzdových složek) = samostatný follow-up přehled později.

Pozn.: SQL pro core 114/115/123 nejsou v lokálních `_phase_*` skriptech (vytvořeny přes
bridge) — při buildu je vytáhnu z `fw.data_set.sql_text` a zabalím filtrem.

## Kód (2 malé změny, deploy) — čeká na rozhodnutí Martina o typu kořene
1. **Brána** `_require_erp_member` (router.py ~292): pustit Dušana i s rolí `employee`.
   Přidat úzký allow-list `_ERP_SCOPED_USERS = {41}` → gate projde.
2. **Whitelist strom** `_build_system_root_from_db` (router.py ~49717): pro `uid in
   _ERP_SCOPED_USERS` použít RESTRIKTIVNÍ WHERE — jen uzly, kde `uid = ANY(visibility_user_ids)`
   (+ kaskáda předků), BEZ broad `parent_only/NULL`. Ostatních se to nedotkne.
   - Varianta A (Marti = uzel v hlavním stromu): nový kořen „🏭 Výroba" (is_immutable=false),
     kopie jako děti, `visibility_user_ids={41}` na kořeni i dětech.
   - Varianta B (Marti = per-user virtuální kořen): kořen „🏭 Výroba" existuje, ale je
     `visibility_scope` skrytý všem a jen Dušan ho vidí přes visibility_user_ids — de facto
     stejné, jen sémantika. (Rozdíl řeší jen to, jestli ho uvidí i rodiče v hlavním stromu.)
3. **Grant**: `visibility_user_ids := array_append(..., 41)` na kořeni Výroba + všech kopiích.

## Poctivá výhrada (Marti to ví)
Stromové zúžení skryje NAVIGACI. Datové endpointy dnes gate jen na membership (ne per-node),
takže technicky zdatný člen by se přímým URL dostal k jinému datasetu. Pro důvěryhodného
vedoucího vlastní firmy = přijatelné; tvrdá zeď = Fáze 2 (per-node ACL, konzultace Marti-AI).

## Po buildu
Instalace PWA u Dušana v Chrome: otevřít `strategie-ai.com/erp` → ikona instalace v adresním
řádku / menu ⋮ → Instalovat → zástupce „STRATEGIE ERP" na ploše (samostatné okno jako .exe).

## Pořadí exekuce (po „jdi")
1. `CLAUDE_PULL_GO` (srovnat lokál) → pak deploy kódu (brána + whitelist).
2. Vytvořit kořen Výroba + kopie přehledů (bridge write / banner) — pull zdroj. SQL, zabalit filtrem.
3. Grant visibility_user_ids=41.
4. Ověřit jako Dušan (impersonace / kontrola stromu), pak instalace PWA.

## Přehled „Docházka — vše" (8.7., bannery #1072–#1074) + DE-DUP zdrojů
Dušanův požadavek: detail odpracovaných úseků VŠECH makačů týmu (kdo/kdy od-do/kolik/na čem),
filtr na makače v gridu — jako Centrála „Docházka - vše" (zdroj `dbo.EC_Dochazka`), ALE včetně
lidí z nové mobilní appky (ti v Centrále chybí).

**Zdroj = `tenant.att_entry`** (pokrývá VŠECHNY: tablet/terminál + mobile_app + manual +
ec_import historie + cssz_dpn), ne work_alloc (jen 7 lidí). Sloupce: smlouva(HPP/OSVČ z
engagement) · čísloZam · jméno · typ(práce/režie/absence) · kategorie · zakázka(project_ref) ·
datum · den · **hodin** · **od** · **konec** · pauza(break_minutes) · stav · **zdroj** · poznámka.

**⚠️ DE-DUP (KONZULTACE Marti-AI, msg 10605 „jdi do toho"):** att_entry má PŘEKRYVY zdrojů
(ec_import × živé = 3565 člověko-dnů, tablet × mobil = 293) → syrový výpis by nafoukl hodiny
(stejný den 2×). Řešení = **priorita zdroje per člověk+den, JEN při zobrazení (žádný přepis
att_entry):**
- Priorita: `manual`(1) > `mobile_app`(2) > `tablet`(3) > `ec_import`(5, gap-fill jen na dny
  BEZ živého) > `import`(6) > `automat`(7); `cssz_dpn`(neschopenky) = zvlášť, vždy; `plan_ec` =
  vyloučeno z detailu.
- Technika: `win AS (SELECT uid, entry_date, MIN(prio) …)` → řádek se ukáže jen když `prio =
  win_prio` (nebo je cssz_dpn). Nesčítat tablet+mobil.
- Ověřeno: raw 20 558 ř / 36 lidí → po de-dup **14 130 ř / 36 lidí, 0 dvojitých dnů**.
- **Vize:** STRATEGIE = zdroj pravdy (živé zdroje = autorita), Centrála/ec_import dohořívá jako
  historie (Marti-AI: varianta B by ztratila historii, není čisté).

## ⚠️ ŽÁDNÁ ŽIVÁ DATA NEMĚNĚNA (revert-safe)
Vše = nové framework řádky (`vyroba.dusan_*` + menu_node podstrom 165) + 2 read-only VIEW
(`tenant.vyroba_dusan_team`, `vyroba_dusan_posts`) + UPDATE JEN na vlastních data_setech.
`att_entry`/`work_alloc`/`EC_Dochazka`/`users` netknuté. Revert recept v paměti
`project_dusan_vyroba_erp_pristup.md` (smazat framework řádky + views + revert kódu; žádná
živá tabulka se nevrací).

## Gotchy dne (8.7.)
- Jirka = **admin (user 20), NE parent** → strom bypass musí být `is_parent_or_admin`, ne jen
  `is_marti_parent` (jinak admin nevidí private uzly).
- Deploy může NErestartovat API A (api_version updated_at se nezmění) → force redeploy.
- Dvě session Claude-28 na stejném stroji SDÍLÍ bridge soubory → kolize (přepisují se);
  write+GO dělat rychle a ověřovat OUT.
- `replace()` do sql_text může nesednout na whitespace → ověřit `ILIKE '%filtr%'`, kdyžtak wrap
  `SELECT * FROM (…) w WHERE`.
