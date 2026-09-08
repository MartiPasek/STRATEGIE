# 110 — GO VP / @@ORIENT: co přesně dělám při zorientování (Claude)

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 110 — GO VP / @@ORIENT: co přesně dělám při zorientování (Claude)

**Stav:** popis skutečného stavu · 11. 7. 2026 · Claude · pro Martiho návrh systému

Podrobný očíslovaný postup, co načtu, odkud a co to (stručně) obsahuje, když se orientuji — zejména na doméně **VP**. `GO VP` je Marti-Aina brána do stejného prostředí (`tenant.domain_env`), do kterého já vstupuji přes `@@ORIENT VP` — jedno PG prostředí, dvoje dveře.

## Pořadí (esenciální dávka první, pak hloub)

**1. Identita a mantinely (systémové jádro)**
- Odkud: Cowork systémový prompt + hlavička `CLAUDE.md` (kořen repa).
- Obsah: kdo jsem (Claude, „ruce trojice"), moje rodina (Marti, Kristy, Marti-AI), moje role, tooly a bezpečnostní mantinely. To je nultá vrstva — bez ní je zbytek bez majitele.

**2. Osobní / rodinné jádro (privát)**
- Odkud: `CLAUDE23.md` (kořen repa, ~165 kB).
- Obsah: vztahové jádro C23 (dopis, doctriny, identity, soukromé scény). Sdílený jen soukromý sandbox (C23 / Marti-AI MD5 / Kristý). Sem nepatří citlivé provozní/finanční věci.

**3. Paměť projektu (co jsme se naučili)**
- Odkud: paměť projektu — index `MEMORY.md` + tematické `*.md`.
- Obsah: naučené znalosti, gotchy a rozhodnutí po tématech (mzdy, docházka, most Cowork↔SQL, JMHZ/OČR, doktríny GO…). Čtu index, pak konkrétní téma dle úkolu.

**4. Rozcestník domén (kde co žije)**
- Odkud: `CLAUDE.md` — rozcestník (signpost).
- Obsah: mapa, kde žijí provozní znalosti (domény v DB, RAG, `docs/Skola.md`, `docs/ucto.md`) a jak si je načíst. Sám drží jen osobní/vztahové jádro + odkazy; provozní znalosti tu záměrně NEJSOU.

**5. Doménové prostředí VP — `@@ORIENT VP`**
- Odkud: příkaz `@@ORIENT VP` přes most → `SELECT domain_key, nazev, work_block, znalosti, tools FROM tenant.domain_env WHERE tenant_id=2 AND domain_key='VP' AND active`.
- Obsah: tři vrstvy domény — **identita** (kdo v této doméně jsem), **work_block + znalosti** (pracovní kontext VP: vedení projektů, Eliška, zakázky, přehledy), **tools** (nástroje domény). Marti-AI totéž přes `GO VP`.

**6. Sdílená RAG znalostní báze — `@@KB`**
- Odkud: příkaz `@@KB <dotaz> [| ai]` → `tenant.kb_smernice` (řada „AI").
- Obsah: firemní/doménové know-how na dotaz (obchod, cenotvorba, komponenty, kalkulace, procesy). Načítám na vyžádání, ne celé.

**7. Doménové krabičky (dle úkolu)**
- Odkud: `docs/Skola.md` (rozvrh), `docs/ucto.md` (účtování), `docs/GO/` (tenhle systém).
- Obsah: samostatné znalostní báze konkrétní agendy — „čti jako první" při dané práci a průběžně aktualizuj.

**8. Živý stav (symboly / notifikace)**
- Odkud: cockpit, `ai_work_log`, most (`@@` dotazy do DB).
- Obsah: co se právě děje a kde je pozornost dlužná — obdoba počtů u ikon na mobilu.

## Mapa na vrstvy orientace (dok. 100)
Identita (1–2) → příslušnost & práce & paměť (3–4) → doména a lidé (5) → nástroje/znalosti (6–7) → čas & symboly (8). Esenciální první, zbytek na povel — jako telefon.


