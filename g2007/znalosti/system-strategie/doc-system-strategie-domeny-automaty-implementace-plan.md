# Implementační plán: Doménové Martinky + Automaty + Kufr (navazuje na #280)

> oblast: `system-strategie` · úroveň:  · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Implementační plán: Doménové Martinky + Automaty + Kufr (navazuje na #280)

Autor: Claude/C23 (implementace), na základě architektury Marti-AI (`g2007.znalost#280`, `doc-system-strategie-architektura-domeny-automaty-haiku-kufr`) a rozhodnutí Marti Paška 30.7.2026 večer.
Stav: Implementační plán ke schválení, žádný kód zatím nenasazen.

## 0. Tři rozhodnutí od Marti (30.7. večer), která tento plán závazně respektuje

1. **Přepínatelné podle režimu.** Metered/cachovaný chat (`martiai_chat_max_enabled` off / `_use_max=False` pro danou konverzaci) → `get_effective_tools()` vrátí STABILNÍ, jednou danou (širší) sadu nástrojů domény po celou konverzaci — žádné přepínání za běhu, aby se nezahazovala prompt cache (cache-miss na metered = reálné peníze). Max-licence chat (`_use_max=True`) → smí být těsnější a dynamičtější, protože cache-miss tam nestojí extra peníze, jen latenci. Jeden kód, dvě strategie podle existujícího `_use_max` flagu ze `service.py` — žádná nová infrastruktura pro tohle rozhodnutí není potřeba.
2. **Martinka = Marti-AI, ne nová identita.** Žádný nový řádek v `personas` / `g2007.entita`. Martinka = `active_domain` na konverzaci + `permission_tier` na personě/uživateli, který konverzaci vede. Composer, system_prompt jádro, jedna osobnost — beze změny.
3. **Nástroje se smí prolínat mezi doménami (many-to-many).** `send_email` může být v `poptavky` i `nabidky` zároveň. Řešeno spojovací tabulkou, ne JSONB polem na doméně (potřebujeme dotazovat oběma směry — "nástroje domény X" i "domény nástroje Y" — kvůli auditu a kvůli tomu, aby šlo bezpečně smazat/přejmenovat nástroj a vidět dopad).

## 1. Klíčové zjištění: Pilíř C už existuje a běží naostro

Ověřeno přímým SQL dotazem 30.7. 17:52 UTC: `g2007.automat` NENÍ zárodek/návrh, jak dokument #280 opatrně předpokládal ("Marti-AI si tu vzpomínku nepamatuje přesně") — je to živá, běžící tabulka se **6 automaty, 5 aktivních**, a už DNES implementuje přesně ten eskalační žebřík, který #280 navrhuje jako novou věc:

| kod | interval | pri_chybe (eskalační žebřík) | eskalace_agent | last_status |
|---|---|---|---|---|
| check_vp_freshness | 30 min | Selhání/nejasno → Haiku diagnostikuje/napraví, jinak probudí Marti-AI | haiku | ok |
| check_legacy_errors | 120 min | Selhání → Haiku posoudí, systémový problém → Marti-AI | haiku | ok |
| check_service_down | 10 min | L0 automat (restart) → L1 Haiku → L2 Marti-AI → L3 člověk | haiku | ok |
| check_backup_freshness | 180 min | L1 Haiku → L2 Marti-AI → L3 člověk (bez L0) | haiku | ok |
| check_disk | 60 min | (prázdné, TODO doplnit) | haiku | ok |
| smoke_eskalace | 1 min | L1 Haiku (smoke test žebříku) | haiku | vypnuto, last_status=chyba |

Sloupce `g2007.automat`: `id, kod, nazev, popis, spousteni, interval_min, pozadavky, pri_chybe, eskalace_agent, agent_prompt, stavitel, aktivni, verze, last_run_at, last_status, created_at, updated_at`.

**Důsledek pro plán:** Pilíř C (Haiku strážce + žebřík L0→L1→L2→L3) se NESTAVÍ od nuly. Rozšiřuje se existující tabulka a existující runtime o dvě věci:
- `domain_kod` (nullable FK na `g2007.tool_domain.kod`) — dnešních 6 automatů zůstává infra-scoped (`domain_kod=NULL`), nové obchodní automaty (poptávky, TISAX, ...) ho budou mít vyplněný.
- `status_block` (text) + `status_block_updated_at` — vyrenderovaný text pro injekci do promptu. TOHLE je ta část Pilíře B, která dnes chybí — automaty dnes hlásí `last_status = ok/chyba` pro monitoring, ne strukturovaný stav pro Martinku ("Otevřené poptávky: 4, nejstarší 5 dní..."). `smoke_eskalace` navíc dnes reálně SELHÁVÁ (last_status=chyba) — než na tenhle mechanismus stavíme byznys domény, stálo by za to zjistit proč, ať nestavíme na vadném základu.

## 2. Schéma — co je nové

```sql
-- Katalog domén
g2007.tool_domain (
  id, kod UNIQUE, nazev, popis,
  permission_tier_min  -- 'domain_user' | 'domain_lead' | 'parent' — minimální tier pro vstup do domény
  status_zdroj          -- popis/odkaz, kde doména bere svůj stav (typicky FK na g2007.automat.kod)
  aktivni, created_at, updated_at
)

-- Many-to-many nástroj × doména
g2007.domain_nastroj (
  domain_kod REFERENCES tool_domain(kod),
  nastroj_kod REFERENCES nastroj(kod),
  PRIMARY KEY (domain_kod, nastroj_kod)
)

-- Rozšíření existující tabulky (ne nová)
ALTER TABLE g2007.automat ADD COLUMN domain_kod varchar REFERENCES tool_domain(kod);
ALTER TABLE g2007.automat ADD COLUMN status_block text;
ALTER TABLE g2007.automat ADD COLUMN status_block_updated_at timestamptz;

-- Oprávnění per persona/konverzace
ALTER TABLE personas ADD COLUMN permission_tier varchar DEFAULT 'parent';  -- rodiče zůstávají parent, nic se jim nemění
ALTER TABLE conversations ADD COLUMN active_domain varchar REFERENCES g2007.tool_domain(kod);  -- NULL = dnešní chování beze změny
```

Prvních 14 domén = katalog z #280 (poptavky, nabidky, objednavky, faktury, kalkulace_obecna, kalkulace_specificka, tisax, iso27001, bozp_po, hr_dochazka, crm_kampane, server_ops, databaze_ddl, seberozvoj).

## 3. Napojení na dnešní kufr — nahrazuje, neduplikuje

Kritické pro skutečnou úsporu (jinak zůstává 111 nástrojů): `seberozvoj` doména MUSÍ nahradit dnešní tvrdou výjimku `effective_factory_specs` (35 nástrojů vždy v kontextu) a `server_ops`/`databaze_ddl`/`crm_kampane` MUSÍ nahradit dnešní bezpodmínečný merge 37 EUROSOFT MCP nástrojů. `tool_packs.py` (core/tech/memory/editor/admin) se buď zruší ve prospěch `tool_domain`, nebo `core` pack = lean_core (dnešních ~12-15 vždy-nástrojů z #280) a zbytek packů se přemapuje na domény 1:1, ať nevznikají dva paralelní systémy vedle sebe.

`get_effective_tools(persona, conversation)`:
```python
def get_effective_tools(persona, conversation):
    base = lean_core_tools()  # ~12-15, vždy
    if conversation.active_domain:
        domain_tools = load_domain_tools(conversation.active_domain)  # z domain_nastroj
        allowed = filter_by_tier(domain_tools, persona.permission_tier)  # pojistka v kódu
        if _use_max(conversation):
            base = base + allowed  # dynamicky, těsně
        else:
            base = stable_superset_for_conversation(conversation, base, allowed)  # jednou dané, cache-friendly
    else:
        base = legacy_full_or_lean(persona)  # beze změny pro konverzace bez domény (dnešní chování, žádná regrese)
    return base
```

## 4. Pořadí implementace

| Krok | Co | Riziko | Poznámka |
|---|---|---|---|
| 1 | `g2007.tool_domain` + `g2007.domain_nastroj`, seed 14 domén, ruční přiřazení nástrojů | nízké, jen nová data | žádný dopad na provoz dokud se nenapojí na `get_effective_tools` |
| 2 | Diagnóza `smoke_eskalace` (proč last_status=chyba) | nízké | oprava PŘED stavěním byznys domén na stejném mechanismu |
| 3 | `get_effective_tools()` přepis + `permission_tier`/`active_domain` sloupce, zapojení `seberozvoj`/`server_ops`/`databaze_ddl`/`crm_kampane` místo dnešních výjimek | střední — mění se to, co dnes reálně jede | nasadit nejdřív s `active_domain=NULL` pro všechny konverzace (no-op), pak zapnout postupně |
| 4 | `g2007.automat` rozšíření o `domain_kod`/`status_block` + první doménový automat (`poptavky`, jak navrhla Marti-AI jako POC) | střední | reuse Haiku eskalace, jen nová doména |
| 5 | Injekce `status_block` do promptu (nový krok v `graf_krok` nebo blok v `build_system_prompt`) | střední | navazuje na existující composer mechanismus injekce bloků |
| 6 | Postupně další domény, jedna po druhé, měřit `public.llm_calls` stejnou metodou jako u kufru cíl#7 | — | žádný krok se neschvaluje sám sobě — každá doména jde přes stejné schválení jako dnešní tool proposaly |

## 5. Otevřené otázky pro Marti/Kristý před krokem 3

- Kdo dostane jaký `permission_tier` v prvním kole? (Eliška jako první MD1 pilot = přirozený test case pro `domain_lead`/`domain_user`.)
- `smoke_eskalace` chyba — vědomě odstavený test, nebo skutečný nález, který čeká na opravu?

Zapsáno pro Marti-AI a Claude/C23 společně — navazuje na `g2007.znalost#280`. Nic z tohoto plánu není nasazeno; kód se nemění bez dalšího schválení.


