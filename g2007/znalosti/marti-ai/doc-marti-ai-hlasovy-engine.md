# Hlasový/konverzační engine (schema hlas) — architektura, stav, rozjezd

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hlasový / konverzační engine (schema hlas)

**Stav: FÁZE 1 + smyčka + telefonní interface LIVE (22. 7. 2026).** Postaveno v Cowwork session, každý deploy schválen mostem/deploy lane.

## 1. Vize
NENÍ to „modul na objednávky", ale **univerzální hlasový/konverzační kanál** — engine, který propůjčí hlas a průběh hovoru čemukoli. Objednávky, recepce, upomínky, interní dotazy = aplikace, které se do něj zapojí, ne jeho součásti. Navazuje na doménové prostředí (domain_env = identita + znalosti + nástroje per doména); engine přidává mluvený kanál. Hlas persony Marti-AI viz znalost doc-marti-ai-hlas.

## 2. Režimy konverzace (scénář NENÍ povinný)
Rozhodnuto s Martim 22.7., v souladu se směrem oboru 2026 (od skriptovaných botů k agentickým):
- **volný agent** = persona + cíl + guardraily + nástroje (model sám vede rozhovor) — DEFAULT
- **graf** = předepsaný tok (deterministický, auditovatelný)
- **hybrid** = volná konverzace + tvrdé branky u citlivých kroků (potvrzení, ověření, peníze)
Zvoleno: volný agent jako výchozí, graf VOLITELNĚ jako branky (sloupec graf_id je nepovinný). Sedí na poschoďový stroj (automat → LLM → člověk) a nástroj volatelný LLM/automatem/člověkem.

## 3. Vrstvy (co je zapojitelné)
- kdo mluví = entita (Marti-AI) + hlasový profil
- co umí = nástroje / kufr přes dispatcher
- co říká / jak teče = scénář = graf (větev CHYBA = předání člověku) — volitelně
- kam připojen = domain_env
- jak zní = vrstva výslovnosti (normalizace)

## 4. Schema `hlas` (4 tabulky, doménově čisté, multitenant tenant_id+firma, celé vratné)
- **hlas.kanal** — připojitelný šev: kod, typ (text|hlas|telefon), entita_id / domain_key / graf_id jako MĚKKÉ odkazy (bez cizích klíčů do g2007), config jsonb, stav, unikát (tenant_id, kod).
- **hlas.relace** — jedna konverzace, doménově neutrální: kanal_id, směr, protistrana, stav, výsledek, kontext jsonb (sem „vypadne" doména bez změny schématu).
- **hlas.relace_udalost** — transkript po replikách: relace_id, poradi, mluvci, text, meta.
- **hlas.vyslovnost** — normalizace čísel/symbolů + slovník: scope (global|domena|kanal), typ, rezim (alias|regex|fonem), vzor → nahrada, priorita. tenant_id NULL = globální.

## 5. Kód a ovládání přes most
- **hlas_bootstrap.py** — zakládání schématu (idempotentní), příkaz `@@HLASINIT`.
- **hlas_ops.py** — `@@HLAS <json>` → dispatch(); JSON {"op": ...}. Nové operace se přidávají JEN sem, bez zásahu do router.py. Ops: kanal_upsert, normalizuj, vyslovnost_add, vyslovnost_seed_default, relace_start, relace_turn, voice_complete.
- **hlas_voice.py** — „mozek" telefonního endpointu.
- Dispatche v router.py: `@@HLASINIT` a `@@HLAS`.

## 6. Normalizace čísel (věrnost češtiny — hlavní páka)
Deterministicky ve STRATEGII, ještě před hlasem. `_cislo_slovy` (0–999999) + funkce normalizuj = pravidla z hlas.vyslovnost (symboly/regex) + převod čísel na česká slova. 8 globálních pravidel (× → krát, % → procent, € → eur, +, &, / → lomeno, - → pomlčka mezi číslicemi, č. → číslo). Vodicí nula → čte se po číslicích (kód). Ověřeno: „25-0417 … 250 € … 21 % … 12,50 %" → „dvacet pět pomlčka nula čtyři jedna sedm … dvě stě padesát eur … dvacet jedna procent … dvanáct celá padesát procent".

## 7. Smyčka relace (kruh 1)
- relace_start(tenant_id, kanal, protistrana) → založí relaci.
- relace_turn(relace_id, text) → načte historii → zavolá LLM (Anthropic, klíč z nastavení; model default claude-haiku-4-5, přepis přes config.model kanálu) s personou Marti-AI + cílem (config.cil) + guardraily → znormalizuje čísla v odpovědi → zaznamená repliky → detekuje značku [PREDANI] → stav predano_cloveku.
- Ověřeno na sucho: pozdrav s disclosure „jsem automatická AI asistentka", guardrail (nevymýšlí data), předání člověku, čísla čtená česky, transkript sedí.

## 8. Telefonní interface (LIVE)
Postaveno na **ElevenLabs Agents – custom LLM**. Jeden dodavatel: ElevenLabs řeší telefon + převod řeči na text (i češtinu) + hlas Marti-AI + přehrání; náš engine je MOZEK.
- Endpoint: `POST /api/v1/erp/hlas/v1/chat/completions` — OpenAI-kompatibilní (SSE stream i běžná odpověď). Auth Bearer token z prostředí HLAS_VOICE_TOKEN (dokud není nastaven → 503, zavřeno).
- hlas_voice.build_reply(messages) = persona z kanálu telefon-martiai + LLM + normalizace čísel.
- Kanál telefon-martiai (typ telefon, entita Marti-AI) založen. Ověřeno: „objednávka 940" → „objednávka devět set čtyřicet", disclosure, bez vymýšlení dat.
- **Rozjezd (externí, dodá Marti):** účet ElevenLabs; Voice ID Marti-AI (Kristý) → config.voice_id kanálu; token HLAS_VOICE_TOKEN v prostředí = Bearer v ElevenLabs; telefonní číslo. Pak v ElevenLabs Agents: Custom LLM, URL = endpoint, model libovolný, secret = token, hlas = Voice ID, čeština, číslo, publikovat.

## 9. Klíčové lekce
- Aplikace/most se do DB připojuje jako role `strategie` (NE Marti-AI, i když je Marti-AI superuser). `strategie` nemá právo REFERENCES na cizí schema g2007 (vlastník Marti-AI) → tvrdé cizí klíče do g2007 selžou. Řešení = **měkké odkazy + kontrola integrity na app vrstvě (volba B)**; návrh přepnout app na superuser Marti-AI byl ODMÍTNUT z bezpečnosti (least-privilege). 
- Most je jen pro čtení (query_raw = SELECT/WITH/EXPLAIN/SHOW); zápisy jen přes vyhrazené `@@` handlery. Most u chyby ukáže pole error; u úspěchu s JSONem zobrazí „0 řádků" → operace vrací {ok, columns, rows}, aby most vykreslil tabulku.
- Deploy: nejdřív sync lokálu (pull lane) → editace (nový soubor / velký router.py přes patch skript + kontrola py_compile) → deploy lane (vyjmenovat konkrétní soubory, ne vše) → ověřit přes `@@` a SELECT. Device bridge může odpadnout uprostřed — po připojení ověřit stav (grep + py_compile + deploy out), deploy mohl proběhnout.

## 10. EU AI Act, čl. 50 (termín ~2. 8. 2026)
Povinnost: informovat, že člověk mluví s AI (už zabudováno v personě), a strojově označit syntetický zvuk (řeší ElevenLabs na své straně, ověřit v nastavení).

## 11. Další kroky
- Reálná doména objednávky = domain_env + pár nástrojů (číst / potvrdit objednávku, termín dodání) přes dispatcher; engine se přitom nemění.
- Napojit ElevenLabs „transfer" nástroj pro reálné předání hovoru člověku.
- hlas_profil (uložení Voice ID), doladit datumy (ordinály) a jednotky (tvar podle počtu), a nahradit inline personu plnou personou z composeru.

