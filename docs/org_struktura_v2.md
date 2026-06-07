# Organizační struktura v2 (vize, Marti 7. 6. 2026)

Marti: *„Musíme udělat organizační strukturu — kdo je vedoucí, komu dát
informaci o přítomnosti/nepřítomnosti, kdo je odpovědná osoba za kontrolu
docházky, kdo schvaluje dovolené… My už ji v EUROSOFTU máme — dělal jsem ji
před 10 lety. Z toho musíme vyjít, jen to učesat a udělat to prodejné pro
další firmy."*

## Co už existuje (DB_EC, ověřeno 7.6.)

| Tabulka | Obsah | Stav dat |
|---|---|---|
| `EC_OrgPost` | posty: Nazev, **ID_NadrazenyPost** (hierarchie), Divize, Poradi, Aktivni | **123 aktivních** |
| `EC_OrgPostZam` | obsazení: ID_Post ↔ **CisloZam**, PlatnostOd/Do, **Zastupce1/2**, StupenZaskoleni/Produkce, Potencialni | **287 aktivních vazeb** |
| `EC_OrgPostKlobouk` | „klobouk" postu: účel firmy/pozice, umístění, předpoklady, **pravomoci, zodpovědnosti** | texty |
| `EC_OrgNapln`, `EC_OrgCinnosti*` | náplně a činnosti postů | |
| `EC_OrgKvalifikace*`, `EC_OrgSmernice*` | kvalifikace, testy, směrnice + přístupnost | |
| `EC_PredavaciProtokolPostu*` | předávací protokoly postu | |

Hierarchie žije: VALNÁ HROMADA → DIVIZE 8 – VEDENÍ FIRMY → MAJITEL / SPRÁVCE
TECHNOLOGIE / FINANČNÍ MANAŽER → … (divizní model, org board).

## Cíl v2 — „učesat a udělat prodejné"

### 1. Generický model ve STRATEGII (tenant.*)

| Tabulka | Z čeho vychází | Poznámka |
|---|---|---|
| `tenant.org_post` | EC_OrgPost | + tenant_id, code; hierarchie parent_post_id |
| `tenant.org_post_assign` | EC_OrgPostZam | employee_id (FK att_employee), platnost, zástupce 1/2 |
| `tenant.org_post_hat` | EC_OrgPostKlobouk | účel/pravomoci/zodpovědnosti (prodejní artefakt — onboarding!) |
| `tenant.org_role_flag` | NOVÉ | per post: `presence_recipient` (komu hlásit ne/přítomnost), `attendance_supervisor` (kontrola docházky), `absence_approver` (schvaluje dovolené…) — **role jako data, ne kód** |

### 2. Resolver „kdo je můj…" (stejný duch jako 4-tier resolver)

`vedouci(employee)` = aktivní assign → post → parent post → jeho aktivní
obsazení (primární, jinak Zastupce1, jinak Zastupce2, jinak o patro výš).
`schvalovatel(employee, role_flag)` = první post směrem nahoru s daným flagem.
Jedna SQL/funkce, používá docházka (notifikace, schvalování), Phase 40
(manager vidí tým), kustod ACL (Fáze 2 práv).

### 3. Napojení na dnešní HR

- Notifikace ne/přítomností: místo hardcoded (1, 11) → `presence_recipient`
  + `absence_approver` z resolveru (fallback rodiče).
- „Kdo kde dnes": sloupec vedoucí; filtr „můj tým".
- Schvalování absencí: tlačítko jen pro `absence_approver`.

### 4. Sync vs vlastnictví

Fáze A (rychlá): jednorázové zrcadlo EC_Org* → tenant.org_* (sync vzor
zakázek — ⚙ ops akce). Centrála 1 zůstává master, Kristý edituje tam.
Fáze B (cílová): správa ve STRATEGII (universal CRUD grids), EC_Org* zamrzne.
Klobouky + kvalifikace + směrnice = samostatná prodejní hodnota (onboarding
balíček pro další firmy).

## Konzultace Marti-AI (7. 6. 2026) — závěry, ZÁVAZNÉ pro implementaci

Dopis: `dopis_marti_ai_org_struktura_v2_konzultace.md`. Marti-AI souhlasí
s modelem (4 tabulky, resolver v SQL, additivní flagy) a přidává:

1. **Q3+** `org_role_flag.priority_order INT` — schvalovací řetězec
   additivně (1 = první, 2 = eskalace…), žádná schema change v budoucnu.
2. **Q2+** Resolver `tenant.resolve_role(employee_id, role_flag) → user_id`
   — SQL funkce v tenant schématu, **navrhne ji Marti-AI** (její DDL).
   Recursive CTE po parent_post_id. Fallback rodiče jako pevný anchor.
3. **Q4+** ACL: org struktura = zdroj pravdy; resolver **deterministický
   a cached**; invalidace cache při změně `org_post_assign`. **Riziko
   neobsazených postů**: fallback po 5 úrovních = `presence_recipient`
   nejvyššího aktivního postu v divizi — jako DB funkce, ne Python.
4. **Q5+** Klobouky: chce je znát a odpovídat („to není rozšíření role
   kustoda — to JE kustod"). Podmínky: čitelný text (`body_markdown`),
   resolver zná primární post, klobouky v jejím RAG scope.
5. **Q6+** Prodejní minimum: tenant_id všude, seed šablona stromu,
   resolver součást balíčku, **klobouk povinný artefakt** (bez něj post
   nemůže být active), žádná hardcoded ID v notifikacích (dnes 1+11 —
   zmizet před prvním zákazníkem). Kvalifikace/směrnice/protokoly =
   prémiová nadstavba Fáze B.
6. **Q7+** Personalizace docházky: scoping `org_post` + `org_division`
   vedle system/user. **Otevřená otázka pro Marti:** člověk se dvěma
   posty — union personalizací, nebo prioritní post?

**Hlavní rizika dle Marti-AI:** neobsazené posty (slepá místa v ACL
a notifikacích) a prázdné klobouky (zmizí onboarding hodnota).

## Další krok

Marti rozhodne dual-post otázku → po prezentaci 8. 6. **Fáze A**:
Marti-AI navrhne DDL + resolver, Claude sync EC_Org* → tenant.org_*
(⚙ ops akce, vzor sync_zakazky), pak přepojení notifikací z hardcoded
ID na resolver.
