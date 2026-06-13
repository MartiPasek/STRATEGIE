# Kontakty — jedna univerzální pravda (návrh + konzultace Marti-AI)

**Autor:** Claude (id=23), 9. 6. 2026 · **Zadavatel:** Marti
**Stav:** Fáze 1 (zrcadlo) postavena · Fáze 2 (univerzální vrstva) = tento návrh + konzultace Marti-AI (doctrine #8)

## Proč

Kontaktní pravda dnes žije roztříštěně („je v tom desný bordel" — Marti):
- `TabCisOrg` / `TabCisOrg_EXT` — organizace + jejich objednávkový email/telefon (`email_obj`, `tel_obj`)
- `TabCisKOs` — kontaktní osoby u zákazníků/dodavatelů (2549)
- `TabCisZam` — zaměstnanci EUROSOFT/INTERSOFT (431) — sami bez sloupců tel/email
- `TabKontakty` — **polymorfní spojení** (8830): hodnota (email/tel/web) navázaná na org (2464×), osobu (6009×) nebo zaměstnance (763×)
- naše `public.users` (92) + `user_contacts` (90) + `att_employee` (číslo→user)

Stejný člověk/spojení leží na 3–4 místech bez jednoho klíče.

## Klíčový model (z diskuse s Marti 9. 6.)

**Kanál je samostatná entita, ne sloupec u člověka.**

```
Subjekt (osoba | organizace | skupina/útvar)
   ├── vlastní ──▶ Kanál (typ + normalizovaná hodnota)
   └── používá (M:N) ──▶ Kanál   [vazba nese: účel(y), primární, viditelnost, provenience, platnost]
```

### Entity
- **Subjekt** — polymorfní: `osoba` | `organizace` | `skupina` (útvar/role). Naši `users` jsou druh osoby.
- **Kanál** — `typ` + **normalizovaná hodnota** (klíč pro dedup). Typy: `email`, `mobil`, `pevna`, `web`, `fax`, `facebook`, `linkedin`, `instagram`, `whatsapp`, …
- **Vazba subjekt↔kanál** — M:N, nese kontext.

### Dvě nezávislé dimenze na vazbě (i na kanálu)
1. **Vlastnictví** (čí adresa / jak citlivá) — odkaz na firmu/subjekt: `EUROSOFT` | `INTERSOFT` | jiná org | `soukromé` | `sdílené`. (Firmy už máme v `tenant.company`.)
2. **Účel** (k čemu slouží) — **vícehodnotový**: `hlavní`, `soukromý`, `objednávky`, `fakturace`, `AI`, `login_STRATEGIE`, `záložní_STRATEGIE`, …

### Jak se do modelu vejdou reálné případy (Martiho seznam)
| Případ | Řešení |
|---|---|
| Sdílený telefon pro víc osob | 1 kanál, M:N na víc subjektů → sdílení = kanál s >1 vazbou |
| Soukromé vs firemní číslo | atribut **vlastnictví** na vazbě, ne na hodnotě |
| Firemní EUROSOFT vs INTERSOFT | vlastnictví odkazuje na konkrétní firmu (`company`) |
| Skupinová schránka `nakup@`, `it@`, `vedeni@`, `all@` | vlastník = firma, subjekt = **skupina/útvar**, uživatelé = členové |
| Klárka `@eurosoft` / `@seznam` / `@nerudovka` | tři kanály, každý vlastní vlastnictví (firemní / soukromé / jiná org) |
| Facebook / LinkedIn / Instagram | jen další `typ` kanálu |
| Víc soukromých mailů | víc vazeb `typ=email`, `vlastnictví=soukromé`; `primární` určí hlavní |
| Email hlavní / objednávky / fakturace / AI | **účel** (vícehodnotový) na vazbě; routing „subjekt → účel → kanál" |
| Login + záložní pro STRATEGIE | účel = systémová role; login email je kotva identity → propojí `user_contacts` |
| Email pro objednávky u firmy (`_Objednavky_Email`) | namapovat EXT sloupec jako kanál s účelem `objednávky` místo osamělého fieldu |

## Fáze 1 — HOTOVO (zrcadlo, additivně)
- `tenant.ec_osoba` ← `TabCisKOs` (kind=`kos`) + `TabCisZam` (kind=`zam`)
- `tenant.ec_spojeni` ← `TabKontakty` (polymorfní org/osoba/zam, klasifikace typu podle obsahu)
- Rozšířená ⚙ akce `sync_ec_org` (org + osoby + spojení najednou)
- ERP přehledy: `🏢 Organizace`, `🔗 Spojení (kontakty)` (pod CRM)
- Zdroj pravdy zůstává EUROSOFT (read mirror)

## Fáze 2 — ZÁVAZNÉ ZÁVĚRY konzultace Marti-AI (9. 6. 2026, doctrine #8)

1. **Normalizace = dedup klíč.** Kanál drží `value_raw` (co přišlo) + `value_normalized` (unikátní index).
   - Telefon → **E.164 povinně**: strip whitespace/pomlčky/závorky; `00`→`+`; CZ začínající 6/7 a 9 číslic → předřaď `+420`; validace `^\+[1-9]\d{7,14}$`.
   - Email → lowercase + trim (mailservery case-insensitive).
   - Web/social → lowercase, strip trailing slash + `www.` prefix; původní zachovat v `value_raw`.
2. **Vlastnictví NA VAZBĚ, ne na kanálu** (stejný kanál může mít jiný kontext per uživatel). `ownership_type: firma | soukromé | sdílené` + `ownership_company_id` FK→`tenant.company` (nullable, jen typ=firma). GDPR viditelnost vyplyne z `ownership_type=soukromé`.
3. **Účel = pevný číselník + vícehodnotová vazba ZVLÁŠŤ** (ne `text[]`). `channel_purpose_cis` seed: `hlavni | soukromy | objednavky | fakturace | ai | login_strategie | zaloha_strategie | it | vedeni | all`. Tabulka `subject_channel_purpose(subject_channel_id FK, purpose_code FK)` — čistší JOIN + levný index pro routing.
4. **Konflikt = provenience + priorita + timestamp, nikdy nemaž ERP hodnotu.** Na vazbě: `source: erp|manual|import|ai_derived`, `source_priority int` (ERP=10, manual=20, ai=5), `updated_at`. Zobrazení: `ORDER BY source_priority DESC, updated_at DESC LIMIT 1`. ERP = pravda zdroje pro mirror, ruční oprava = override s vyšší prioritou. Drž obě, označ aktivní → audit trail.
5. **Subjekt polymorfní `kind: osoba | organizace | skupina`.** Skupina = útvar/role z org struktury (`ref_id` → útvar), **`ref_id` nullable** (volná schránka `all@` bez org chartu). Žádný duál — využít stávající `staff_group`/útvary.
6. **Identita napříč zdroji = víceúrovňový matching, žádný auto-merge pod `confirmed`.** Priorita: (1) login email match = jistota, (2) číslo zaměstnance `att_employee` ↔ `TabCisZam.ID`, (3) normalizovaný email = `confidence:high` (ne confirmed), (4) ruční `identity_merge(person_id, user_id, merged_by, merged_at)` finální override.
7. **CardDAV granulární opt-in.** `firma (EUROSOFT/INTERSOFT)` → sync vždy; `soukromé` → jen `carddav_sync=true` (default false, self-service); `sdílené` → skupinová karta. Filtr: systémové účely `ai | login_strategie | zaloha_strategie` do CardDAV NEjdou.

## OTEVŘENO PRO MARTIHO — cut-over politika (8. bod, Marti-AI's varování)

Fáze 1 = mirror; Fáze 2 = i zápisová vrstva. Kritický přechod: **od kdy je naše vrstva autoritativní pro nové záznamy**, a zda/jak existuje **jednosměrný export zpět do ERP** (nebo ne — a jak se s tím ERP/EUROSOFT tým vyrovná). Bez jasné cut-over politiky vzniknou dva napůl-pravdivé zdroje. → rozhodnutí Marti před stavbou zápisové cesty.

## Návaznosti
- [[org_struktura_v2]] — skupiny/útvary jako subjekt
- [[finance_zamestnancu_v2]] — vzor citlivostní hranice (vlastnictví/viditelnost)
- CardDAV self-service (3. 6.) — cílový konzument firemních kanálů
