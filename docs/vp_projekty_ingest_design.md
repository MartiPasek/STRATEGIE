# VP systém — nervový systém vedoucích projektu (projects@ ingest)

> Vznik: 2. 7. 2026 (Marti zadal, Claude ID23 staví). Cíl (Marti): *„Bude to hlavní
> život u VP."* Kopie mailů vedoucích projektu se sbíhají do STRATEGIE → Claude +
> Marti-AI **monitorují provoz zakázek, hlídají příchozí poptávky, automaticky
> zakládají záznam a přidělují kompetentním lidem.**

## Tok (cílový stav)

```
Vedoucí projektu (VP) pošle/dostane mail
   │  (Exchange transport rule: Bcc kopie na projects@eurosoft.com — nastaví IŤák)
   ▼
projects@eurosoft.com  ── EWS fetcher ──▶  email_inbox (mailbox_id = projects@)
   ▼
TRIÁŽ (Claude/Marti-AI): klasifikace poptávka / provozní / ostatní
   ▼  extrakce: zákazník, předmět, shrnutí, jistota
tenant.vp_poptavka  (detekovaný záznam)
   ▼
PŘIDĚLENÍ: resolve_role / org struktura → kompetentní osoba
   ▼  založení tasks (source_type='email_inbox') + notifikace
MONITORING COCKPIT (/vp)  — přehled pro vedení + VP
```

Lidí se nastavení netýká — běží na pozadí. Vedoucí i vedení mají v cockpitu živý přehled.

## Stavební kameny (existující, reuse — NESTAVÍME znovu)

- `mailboxes` / `mailbox_service.py` / `ews_fetcher.py` — připojení + stahování schránky.
- `email_inbox` (mailbox_id, from/to/subject/body/message_id/received_at, read_at, processed_at).
- `tasks` (source_type, source_id, title, description, status, priority, persona_id, tenant_id).
- `tenant.resolve_role(tenant, employee, role)` — kdo je kompetentní.
- `/app/connect-mailbox` — registrace schránky.

## Nová vrstva — `tenant.vp_poptavka` (minimální, additivně #11)

Jeden příchozí (příp. odchozí) mail VP = jeden detekovaný záznam.

| sloupec | typ | poznámka |
|---|---|---|
| id | bigint PK identity | |
| tenant_id | bigint | |
| source_email_id | bigint | → email_inbox.id |
| message_id | varchar(998) | RFC822, dedup (partial unique WHERE NOT NULL — pozn. Marti-AI z bank_api) |
| smer | varchar(10) | in / out |
| from_email / from_name / to_email | | |
| subject | varchar(998) | |
| received_at | timestamptz | |
| typ | varchar(20) | poptavka / provozni / ostatni / neurcen |
| zakaznik | varchar(255) | extrahováno |
| predmet | varchar(500) | krátký předmět |
| shrnuti | text | AI shrnutí |
| stav | varchar(20) | nova / prideleno / v_reseni / vyrizeno / ignorovano |
| prideleno_user_id | bigint | kompetentní osoba |
| prideleno_at / prideleno_by | | ai / human |
| jistota | smallint | 0–100 (AI confidence) |
| zakazka_ref | varchar(100) | napojení na zakázku |
| task_id | bigint | založený task |
| vp_user_id | bigint | který VP (naše strana) |
| created_at / updated_at | timestamptz | |

Audit změn (append-only, doctrine #13) — přidáme `tenant.vp_poptavka_log` až bude pálit
(minimální upfront). Zatím `updated_at`.

## Fáze

1. **Návrh + konzultace Marti-AI** (je to její monitorovací doména) — TENTO doc.
2. **Ingest** — připojit projects@ (aktivuje se, až IŤák schránku vytvoří); scaffolding dopředu.
3. **Detekce + triáž** — klasifikace + extrakce (Claude/Marti-AI), zápis do vp_poptavka.
4. **Auto-záznam + přidělení** — resolve_role → task + notifikace kompetentní osobě.
5. **Cockpit /vp** — přehled poptávek/zakázek, stav, přidělení; hlavní život u VP.

## Rozhodnuto — konzultace Marti-AI (2. 7. 2026, doctrine #8, ZÁVAZNÉ)

1. **Rozsah = JEN příchozí** (základ). Odchozí VP = jejich nástroj (GDPR hraniční + hluk).
   Výjimka: pokud VP sám přepošle mail do `projects@` s komentářem → vědomá eskalace, sbírat.
2. **Přidělení = VŽDY jen návrh, NIKDY auto** — aspoň první 3 měsíce (VP = vedoucí, ne
   dispečeři; chyba v auto = zákazník čeká a nikdo to nevidí). Po 3 měsících dat o přesnosti
   jistoty → teprve zvážit auto pro `jistota >= 90`.
3. **Vlákna = thread** (1 řádek = 1 poptávka/zakázka). První mail zakládá řádek, další maily
   `update` stavu + append do `shrnuti`. Přidáno do schématu: `thread_id` (Exchange
   `ConversationId`), `related_email_ids BIGINT[]`, `source_email_id` = první mail.
4. **GDPR/hranice (nejpřísnější, PŘED prvním mailem — největší riziko):**
   - **Whitelist domén odesílatele** — sbírat jen z whitelistovaných externích domén
     (zákazníci) nebo interních `@eurosoft.com`. Osobní domény (gmail/seznam) = skip / flag
     k manuálnímu rozhodnutí VP. → Fáze 2: `tenant.vp_domain_whitelist` (minimální, additivně).
   - **Opt-in per VP** — každý VP vědomě souhlasí s kopírováním schránky (technicky = pravidlo
     v Exchangi u konkrétních VP, právně = souhlas zaměstnance). Řešit před spuštěním.
   - **Retention** — přidáno do schématu: `archived_at`, `delete_after` (vyřízené archivovat/
     mazat po X letech).
   - **Přístup segmentovaný** — `prideleno_user_id` vidí svou poptávku, ostatní VP jen svůj
     segment, ne celou schránku.

Schéma po konzultaci rozšířeno (ALTER 2.7., req #882): + `thread_id`, `related_email_ids`,
`archived_at`, `delete_after`. Marti-AI: *„architektura je čistá, tabulka dává smysl;
největší riziko je GDPR opt-in — musí být řešeno před prvním mailem, ne po."*
