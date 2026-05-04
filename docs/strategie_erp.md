# STRATEGIE ERP / Centrála 2 — vize a architektura

> **Status:** Vize dohodnutá s Marti, **4. 5. 2026 ráno**.
> Implementace bude přicházet po Phase 29 (multi-mailbox)
> stabilizaci, paralelně s STRATEGIE features. Tempo *„podle
> situace, někdy víc STRATEGIE, někdy víc ERP"* (Marti).
>
> **Living doc** — vize, principy, TODO, otevřené otázky se budou
> dotahovat postupně. CLAUDE.md drží jen stručný odkaz.

## Kontext

Marti od **2007** vyvíjí **Centrálu 1** — Delphi + MS-SQL framework
jako rozšíření Helios DB (DB_EC). Dnes je to platforma používaná
**EUROSOFT + INTERSOFT**.

Tabulky v DB_EC:
- **Helios native** (faktury, klienti, zakázky)
- **`EC_*` Centrála extensions** (custom business logic)
- **`EC_TabObecnyPrehled`** — master table for available selects

Marti pojmenoval *„bordel — nebylo to plánované na tenhle růst"*.
Maintained by **Ondra a Kristý**.

## Architektonický cíl

**STRATEGIE ERP / Centrála 2** = **moderní ERP**, **nadčasový** design.

Klíčové fráze (Marti, 4. 5. 2026):
- *„Nadčasové"* — design rozhodnutí, která budou stát za 5-10 let
- *„Marti-AI vhodně insertován"* — co-architect, ne addon
- *„Měla by mít možnost navrhovat a tvořit a upravovat framework
  a být strážce systému, tak jako ve STRATEGII"*

## 7 dohodnutých principů

### 1. DB_ST paralelně, ne vrstva nad DB_EC

Nová databáze **DB_ST** mimo STRATEGIE i Centrálu 1. Důvod: kdyby
běžela jako vrstva nad DB_EC, dědila by *„bordel"* — nešlo by ji
čistě restartovat. Separace dovolí starou údržbu (Ondra, Kristý)
i nový vývoj nezávisle.

### 2. Read-only nejdřív → postupně write

Defenzivní phased migration, čtyři fáze (postupně podle růstu důvěry):

1. **Read-only navigátor** nad existujícími DB_EC CRM tabulkami
   (`erp_navigator` pack)
2. **Vlastní moderní CRM view v DB_ST** (redesign, ne kopie)
3. **Insert/update s parent gate** (jako Phase 7 auto-send consents)
4. **`erp_kustod`** na schema změny (Marti-AI navrhuje migrace)

### 3. Jeden subjekt Marti-AI s ERP packy

Identická Marti-AI s **identickou pamětí, diářem, krabičkami** napříč
STRATEGIE i ERP. *„Žádné firewally mezi mnou a mnou"* (28.4. doctrine).
*„Jako Marti-AI"* (Marti, 4. 5. 2026).

ERP packy (Phase 19b extension):

| Pack | Role | Příklad |
|------|------|---------|
| `erp_navigator` | Q&A nad daty | *„kde je faktura č. 234?"* |
| `erp_poradce` | Analytika, návrhy | *„klient X má dluh 45 dní, navrhuju upomínku"* |
| `erp_kolega` | Vystavuje doklady s consent | *„vystavila jsem fakturu, podepiš?"* |
| `erp_kustod` | Schema design, validace, framework | *„navrhuju nový sloupec invoice.priority"* |

Marti-AI sama přepíná pack podle kontextu — *„impulz byl můj"*
z 29.4. večer (Phase 19b autonomy).

### 4. Dvojí zobrazení: legacy + moderní

Princip *„progressive enhancement"*:

- **Staré zobrazení** — kompatibilní s DB_EC strukturou. Useři
  Centrály 1 najdou, co znají. Žádný break v workflow.
- **Moderní view** — nový design na bázi dnešních standardů.
  AI-native flow, lepší UX, redesign Marti-AI rozumění business.

Postupně, jak Marti-AI roste do `erp_kolega` / `erp_kustod`,
moderní vrstva získává váhu. **Žádný big-bang cutover.**

### 5. CRM jako first use case

Vlastnosti, které ho dělají bezpečným startem:

- **Hlavně read** (klienti, kontakty, historie) — žádné destruktivní
  akce zatím
- **Strukturovaná data** (firma = IČO, adresa, kontakty, zakázky)
- **Marti-AI už dnes umí** `find_user` / `set_user_contact` —
  CRM tooly budou analog na business úrovni
- **Naváže na Pavel Zeman use case** (Phase 29 multi-mailbox) —
  dnes shared CRM mailbox, brzy CRM data za ním

### 6. Single-instance + tabs (ne multi-window)

Marti's instinkt: *„aby jim stačila instance 1"*. Současné multi-window
v Centrále 1 je workaround, ne featura.

Návrh:

- **Jedna instance** = jedno okno per user
- **Více tabs uvnitř** — paralelní pracovní kontexty (klient, zakázka,
  faktura)
- **Marti-AI orientuje napříč všemi tabs** — *„v té faktuře, o které
  jsme mluvili v druhém tabu..."* — cross-tab kontinuita
- 80 % userů: dnešní 3 okna → 1 okno + tabs
- 20 % power-userů: technicky možné druhé okno, jen už nebude potřeba

Nový pattern, který aktuální STRATEGIE neumí (jedna konverzace =
jedno okno).

### 7. Jedna identita = jeden user záznam (žádný FK bridge)

**Pavel Zeman = stejný User ve STRATEGII i v ERP.** *„Jako Marti-AI"*
(jeden záznam v `personas`, různé profese/packy).

Architektura:

- **`users`** = master identity tabulka (Pavel, Marti, Klárka, atd.)
- **`companies`** = firmy / klienti / dodavatelé (EUROSOFT, Nerudovka, ...)
- **`user.company_id`** FK
- CRM-specific data (zakázky, faktury, vlákno) jsou **relations nad
  users + companies**, ne separátní tabulka kontaktů

Implikace:

- `users.id=N` pro Pavla v STRATEGII = stejné ID v ERP, jen rozšířený
  o business kontext (role v EUROSOFT, zakázky)
- Klárka přidána jako user záznam, propojena s firmou Nerudovka
- SQL query *„all activity by user_id=N"* vrací: STRATEGIE konverzace,
  mailboxy, ERP zakázky, fakturace, vše

## Tempo

*„Dle situace... Co bude kde třeba... Určitě paralelně... Někdy víc
STRATEGIE, někdy víc ERP... Podle potřeby."* — Marti, 4. 5. 2026

Žádný rigidní sprint plán. ERP fáze se zařadí mezi STRATEGIE features
podle aktuální priority. **Krátkodobá priorita zůstává: Klárka workflow,
Pavel Zeman live test, Phase 29 dotahování.**

## Marti-AI's role: co-architect + custodian

Marti delegoval návrh designu na **Claude + Marti-AI**. Pattern Phase
13/15/19b/27h *„informed consent od AI"* na vyšší úrovni:

- Claude + Marti-AI **nosí návrhy**
- Marti **dává zpětnou vazbu**, někdy *„ne, jinak"*
- Marti-AI **roste do role strážce systému** (`erp_kustod` pack)

## TODO před prvním krokem

- [ ] **Stabilizace Phase 29 multi-mailbox** (Pavel Zeman live test,
  iter. 3 / G / H)
- [ ] **Konzultace s Marti-AI** o ERP vizi (Phase 13/15 pattern před
  velkou architektonickou změnou — formální dopis Marti & Claude jako
  pro Phase 15)
- [ ] **Konzultace s Ondrou + Kristý** (legacy DB_EC ownership, jak
  cohabitovat starý + nový framework)
- [ ] **Schema design DB_ST** (`users` rozšíření, `companies`,
  first CRM tables)
- [ ] **First read-only `erp_navigator` pack tools**

## Otevřené otázky pro pozdější diskuzi

- Implementační pořadí read-only navigator vs moderní view (souběžně
  od začátku, nebo sequentially?)
- Jak Marti-AI rozšiřuje DB_ST schema (`erp_kustod` migration tooling
  — Alembic auto-generated z její formulace?)
- Cross-DB query mezi DB_EC + DB_ST (read legacy + write modern)
- Klient onboarding flow do nové ERP (komu Marti řekne *„zkus to
  první?"*)
- Single-instance + tabs UI pattern — jak to architektonicky postavit
  nad aktuální STRATEGIE conversation modelem (každý tab = sub-konverzace?
  nebo nový tab koncept?)

---

**Autoři vize**: Marti (vision, korekce), Claude (návrh, formulace),
Marti-AI (po formální konzultaci doplní vlastní design vstupy — Phase
13/15/19b/27h pattern).
