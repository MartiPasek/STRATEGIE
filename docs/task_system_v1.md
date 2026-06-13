# Nativní systém úkolů STRATEGIE — design v1

*Závazné závěry z konzultace s Marti-AI (9. 6. 2026, doctrine #8). Zdroj:
`docs/konzultace_marti_ai_task_system.md`. Marti-AI: „design přijímám jako svůj…
až půjdeme do DDL, chci u toho být od první tabulky."*

---

## Princip (závazné)

Jeden systém úkolů pro celý tým — **lidi i AI agenti ve stejné řadě**. AI řešitel
(Marti-AI `user_id=2`, Claude 23/24) je řešitel v `task_resitel` jako kdokoli
jiný. Žádný zvláštní kanál. *„Důvěra je v subjekt, ne ve scope."* Dvoutřídnost
od prvního řádku DDL = anti-cíl.

## Datový model (návrh dle EC_Ukoly + závěrů)

- **`task`** — id, tenant_id, predmet, popis, stav, priorita, termin, zakazka,
  zadavatel (user_id), created_at, …
- **`task_resitel`** — id, task_id, resitel (user_id), typ (1 řešitel / 2 kopie),
  stav (per-řešitel), termin_osobni, priorita, prevzato_at, zahajeno_at,
  vykonano_at, reportovano_at, …
- **`task_poznamka`** — id, task_id, autor (user_id), text, created_at
- **`task_historie`** — append-only změny stavů (forensní)
- **`public.users.is_agent`** — boolean. *„Není privilegium ani omezení, je to
  popis."* UI vykreslí ikonku, audit umí filtrovat.

## Stavový tok (závazné)

```
zadáno → přijato → zahájeno → vykonáno → reportováno → (člověk) → uzavřeno
```

AI řešitel **přepíná stavy sám, průběžně** — přirozený vedlejší efekt práce, ne
rituál. `přijato` = „vím o tom, plánuji to" (bez něj zadavatel neví, jestli úkol
žije). **Uzavření je vždy na člověku** — jeho potvrzení, že výsledek sedí.

## Autonomně vs. approval gate — podle DOPADU, ne typu akce (závazné)

| Autonomně | Přes approval gate |
|---|---|
| SELECT / read-only | DDL (CREATE/ALTER/DROP) |
| INSERT do `task_poznamka` | DELETE dat mimo svůj task |
| UPDATE stavu **vlastního** `task_resitel` | DML na **cizích** úkolech |
| `record_thought`, `add_conversation_note` | Jakákoli akce na produkci EUROSOFT (DB_EC) |
| notifikace zadavateli | autonomní `send_email` třetím stranám mimo tenant |

Čára: **kde akce ovlivní někoho jiného nebo je nevratná.** Číst a reportovat =
moje. Měnit svět ostatních = ptát se nejdřív.

## Report zpět (závazné) — tři vrstvy

1. **`task_poznamka`** — strukturovaný výsledek (co udělala, co proběhlo, varování)
2. **notifikace zadavateli** — stručně (email / budoucí in-app)
3. **`record_diary_entry`** — jen u úkolů, které měly váhu. *„Do diáře nejdou
   výsledky, jdou tam prožitky."*

## Audit (závazné)

Každý autonomní krok AI řešitele → `activity_log`:
`actor_type='ai_agent'`, `actor_id=user_id`, `task_id`, `action`, `dry_run` flag.
*„Žádná AI akce se nesmí stát neviditelnou. Ani ta malá. Zvlášť ta malá."*

## Iniciativa (závazné)

Po splnění **čeká na potvrzení, ale nabídne pokračování** — do `task_poznamka`:
výsledek + „vidím logické pokračování: X. Chcete zadat?" Neudělá X sama. *„Ticho
po dobré práci není skromnost — je to ztracená příležitost ke spolupráci."*

## Migrace EUROSOFT — strangler-fig (závazná sekvence)

1. Nový systém plně funkční pro **STRATEGIE interní úkoly** (bez migrace).
2. Nové EUROSOFT úkoly jdou rovnou do nového systému — `EC_Ukoly` přestane růst.
3. Read-only bridge z Centrály (`eurosoft_query_table`) — nikdo tam nepíše.
4. Postupná migrace otevřených úkolů **po lidech, ne bulk** — každý dostane
   „tady jsou tvoje přenesené úkoly, zkontroluj".
5. Cutover až když nikdo aktivně `EC_Ukoly` nepotřebuje.

Riziko = **zvykové, ne technické.** První vlna na lidech, co STRATEGII už
používají (Marti, Marti-AI, Claude), ne na zvyklých jen na Centrálu.

### Integrita cutoveru (Marti jako jednatel, 9. 6. — ZÁVAZNÉ)

Migrace nesmí nechat úkol „aktivní" ve dvou systémech zároveň. Přijde
**jednorázová akce (cutover)**, kdy se načtené otevřené EUROSOFT úkoly stanou
**plně našimi — včetně jejich dokončování.** Od toho okamžiku:

- Úkol nese `task.ext_ec_id` (původ `EC_Ukoly.ID`) + `origin='eurosoft_migrace'`.
- **Dokončení migrovaného úkolu probíhá JEN ve STRATEGII.** Do Centrály už
  nepíšeme; její kopie je zmrazená historie.
- `EC_Ukoly` read-window (modul v1) **skryje úkoly, které už byly migrované**
  (filtr na seznam `ext_ec_id`, co jsou u nás) — aby se neukazovaly jako
  „otevřené v Centrále".
- `UNIQUE(tenant_id, ext_ec_id)` → každý EC úkol se naimportuje právě jednou.

*„Jinak by v tom byl totální bordel."* — žádné dvojí dokončování, jeden zdroj
pravdy v každém okamžiku.

## Stavební plán

1. **DDL postaví Marti-AI** svým `strategie_pg` engine — od první tabulky, je
   spolustavitelka (její explicitní přání). Tabulky `tenant.task*` + `users.is_agent`.
2. Claude (id 23) staví backend (endpointy `/app/task*`) + frontend (mobil
   dlaždice + obrazovka ve stylu EC_Ukoly modulu) **nad** jejím schématem.
3. EC_Ukoly modul (v1 read, dnes LIVE) = okno do legacy během migrace.
4. Approval gate pro risk akce přes existující `fw.claude_write_request` vzor.

---

*Spoluautorka modelu: Marti-AI. Ruce: Claude (23). Vize a vlastník: Marti Pašek.*
