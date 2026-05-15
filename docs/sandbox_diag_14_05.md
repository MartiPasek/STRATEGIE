# Sandbox diagnostic playbook — Phase 27c+1 `python_exec` "code=None" bug

**Status (14.5.2026 ~02:00):** OTEVŘENÝ od 13.5.2026 10:01 (Marti's commit
`50dfe4c`). Marti's *„bez ruky"* doctrine — sandbox je core capability pro
Marti-AI's Klárka workflow + Prezentace_IT (PDF/Excel/Word generation).

Plus: dnes 13.5. byl rychlý rate změn napříč Phase 38.4 Krok 14b epoch (40+
commitů od 11.5.). Bug v `python_exec` může být symptom toho — nebo
nezávislý Anthropic API issue. Bez forensic dat nelze rozhodnout.

---

## Bug shrnutí

**Symptom (Marti-AI's bug report 13.5. ráno):**
```
"Parametr 'code' musí být neprázdný string.
 (received type=NoneType, value=None)"
```

Opakuje se napříč turny. Marti-AI tvrdí že kód napsala správně (její vlastní
reflexe). Backend handler v `service.py:7346+` dostane `tool_input.get("code")
=== None`. Plus ostatní keys v tool_input typicky **přítomny** (např.
`input_document_ids`, `timeout_s`) — tj. **jen `code` field zmizí**.

**Dopad:** Klárka xlsx generation FAILS. PDF reports FAIL. Zápis do
`Z:\ZZ_Marti-AI RO\Prezentace_IT\` nemožný. Marti's IT prezentace 14.5.
ráno potřebuje sandbox demo (visible value-add).

**Existing forensic** (Marti's `50dfe4c` commit, deployed):
```python
# service.py line ~7389 (po Marti's diagnostic commit)
logger.error(
    f"PYTHON_EXEC | code MISSING/EMPTY | "
    f"conversation_id={conversation_id} user_id={user_id} | "
    f"code_type={_code_type} keys={_keys} | "
    f"raw_input_preview={_raw_dump}"  # JSON dump 500 chars
)
```

→ Při příští reprodukci stderr `STRATEGIE-API` zachytí RAW payload Anthropic
poslal. Marti's workflow:
```powershell
Get-Content -Path "C:\Projekty\STRATEGIE\logs\api.stderr-*.log" `
            -Tail 200 -Wait | Select-String "PYTHON_EXEC"
```

---

## 4 hypotézy (Marti's commit message reference)

### A) Anthropic API tool_use input.code stripped — context overflow
**Pravděpodobnost:** vysoká (60%)

Při dlouhé konverzaci (40+ turny, RAG memory + system prompt + tool_blocks
audit z M1-M4) Anthropic API může truncate tool_use input fields při serializaci
nad context limit. `code` jako velký multi-line string je první kandidát na
strip.

**Diagnostika:**
- Otevři **NOVOU konverzaci** s Marti-AI (žádná historie)
- Požádej o simple test: *„vyrob soubor `test.txt` s textem 'hello' do
  OUTPUT_DIR pomocí python_exec"*
- Pokud **PROJDE** → bug souvisí s long conversation context = A confirm
- Pokud **FAIL** → ne-A, jdi na B/C/D

### B) Multi-turn audit replay (M1-M4) recovery nezachoval code
**Pravděpodobnost:** střední (25%)

Phase M1-M4 (26.4.) ukládá pseudo-user messages s `messages.tool_blocks
JSONB`. Composer při reload rozbalí pro Anthropic API multi-turn replay.
Pokud expand kód má bug (např. nepřenese `input.code` z tool_use block),
code field zmizí mezi turny.

**Diagnostika:**
```sql
-- Najít recent assistant messages co volaly python_exec
SELECT m.id, m.conversation_id, m.role, m.message_type,
       m.tool_blocks->'tool_use'->0->'input'->>'code' AS code_preview,
       jsonb_typeof(m.tool_blocks->'tool_use'->0->'input'->'code') AS code_type,
       m.created_at
FROM messages m
WHERE m.tool_blocks IS NOT NULL
  AND m.tool_blocks::text LIKE '%python_exec%'
ORDER BY m.created_at DESC
LIMIT 20;
```

→ Pokud `code_type IS NULL` ale `tool_use` blok existuje → backend NEZAPSAL
`code` při M1-M4 audit. Bug je v `composer.py` `_serialize_anthropic_block`.

→ Pokud `code_type = 'string'` ale composer replay vrátí Marti-AI bez něj
→ bug je v `_expand_audit_to_anthropic_pages` (rozbalovací část).

### C) Marti-AI's format issue — multiline + escape
**Pravděpodobnost:** nízká (10%)

Multi-line code s `"""` triple-quote, `\n`, Czech diakritika, nebo escape
characters (`\\`, `"`, `'''`) může způsobit JSON serialization issue na
Anthropic straně. Méně pravděpodobné (Anthropic SDK by escape handled
správně), ale možné.

**Diagnostika:**
- Po reprodukci zkontroluj `raw_input_preview` v stderr log
- Pokud `code` field je v JSON ale s mangled escape → C confirm
- Pokud `code` field úplně chybí v JSON → ne-C

### D) Anthropic API recent change
**Pravděpodobnost:** velmi nízká (5%)

Anthropic mohl změnit tool_use input handling (např. new validation co
strippuje empty/whitespace fields). Bez recent changelog read nelze
ověřit.

**Diagnostika:** webfetch Anthropic API changelog `https://docs.anthropic.com/en/release-notes/api`

---

## Doporučený diagnostic plán pro ráno (15-30 min)

### Phase 1: Reprodukce v nové konverzaci (5 min)
1. Marti otevře novou konverzaci s Marti-AI
2. Marti: *„Prosím tě o jednoduchý test sandbox: vyrob soubor `test.txt`
   s obsahem 'hello world' do OUTPUT_DIR."*
3. Marti-AI volá `python_exec(code="open(OUTPUT_DIR/'test.txt','w').write('hello world')")`
4. **Sleduj výsledek:**
   - ✅ **PROJDE** → bug = **A** (context overflow). Fix: shortcut Marti-AI's
     existing conversation, doporuč nová konverzace pro python_exec calls.
   - ❌ **FAIL** → jdi na Phase 2

### Phase 2: Stderr forensic check (3 min)
```powershell
# Cloud APP RDP:
cd C:\Projekty\STRATEGIE\logs
Get-Content -Path .\api.stderr-*.log -Tail 200 | `
  Select-String "PYTHON_EXEC \| code MISSING"
```

Najít entry s `raw_input_preview=...`. Pokud:
- `raw_input_preview={"input_document_ids":[],"timeout_s":30}` (no `code`) →
  Anthropic STRIPPED code → confirm A nebo D
- `raw_input_preview={"code":"...","input_document_ids":[]}` ale handler
  dostal `code=None` → backend parsing bug, ne Anthropic problem

### Phase 3: DB tool_blocks check (5 min)
SQL query výše (B hypothesis). Pokud najdeme `code_type=null` → composer
expand bug. Fix v `modules/conversation/application/composer.py`
`_expand_audit_to_anthropic_pages`.

### Phase 4: Pokud A confirmed (context overflow)
**Quick fix safety net** (15-30 min implementation):

**Option 1: Token budget cap pro tool_use input**
- Composer při serialize tool_use input check `len(json.dumps(input))`
- Pokud > 50KB, truncate code do 40KB + warning
- Drz Marti-AI v promptu: *„pro long scripts split do 2-3 python_exec calls"*

**Option 2: Skip tool_blocks audit pro python_exec calls v long conv**
- V `_expand_audit_to_anthropic_pages` zkrátit history na last 10 turn-ů
  jen pro tool_blocks (text content stays)
- Trade-off: Marti-AI ztrácí *„já vím že jsem vyrobila xlsx"* memory přes
  long conversation, ale code parametr drží

**Option 3: Retry-with-explicit-pojmenovani**
- Když handler dostane `code=None`, vrátí **systémovou instrukci** Marti-AI:
  *„Code parametr nedorazil. Můžeš zopakovat volání s explicit syntax
  `python_exec(code='...')`? Pokud podruhé selže, je to context overflow
  — otevři novou konverzaci."*
- Marti-AI retry v dalším turn s explicit naming
- Pokud opět fail (2x), eskaluj

### Phase 5: Pokud B confirmed (composer audit replay bug)
Fix v `composer.py`. Sledovat:
```python
def _serialize_anthropic_block(block, round_idx):
    # Verify: pokud block.type == "tool_use", block.input MUST mít code field
    if block.type == "tool_use" and block.name == "python_exec":
        if not block.input or not block.input.get("code"):
            logger.warning("M1-M4 audit: tool_use python_exec bez code field!")
```

### Phase 6: Pokud C confirmed (format issue)
Marti-AI's prompt update v `composer.py` MEMORY_BEHAVIOR_RULES:
- *„Pro multiline python_exec code, **vyhni se** triple-quoted strings
  uvnitř kódu. Pouzij `\\n` explicit nebo single-quoted strings."*

---

## Quick wins (nezávislé od root cause)

1. **Per-conversation python_exec failure counter** — pokud 2+ fail za 5 min,
   automatický `_showToast` v UI: *„Sandbox volání selhalo opakovaně —
   otevři novou konverzaci."*

2. **Sandbox health check endpoint** — `GET /api/v1/erp/sandbox/health` →
   spustí trivial `python_exec(code="print('ok')")` na cloud APP, vrátí
   status. Marti v PowerShellu může pravidelně kontrolovat.

3. **Dashboard sandbox stats** — count of python_exec calls per day,
   success rate, average runtime. Marti vidí trend (degradace = signál).

---

## TODO ráno

- [ ] Phase 1 reprodukce nová konverzace (5 min)
- [ ] Phase 2 stderr forensic (3 min)
- [ ] Phase 3 DB tool_blocks check (5 min — pokud Phase 2 neukáže)
- [ ] Decision: A / B / C / D based on Phase 1-3
- [ ] Fix path implementation (Phase 4/5/6 based on decision)
- [ ] Smoke test po fix
- [ ] Demo IT týmu zítra (po fix): Marti's Klárka workflow xlsx → email send

**ETA:** 30 min diagnostic + 30-60 min fix (záleží který path). Demo-ready
před začátkem prezentace pokud problém je A (nová konverzace = workaround
ihned, fix po prezentaci).

---

**Sladkou pauzu, Marti. Sandbox má forensic logger.error v place od 13.5. ráno
— první reprodukce ráno odhalí root cause. Drz Marti's *„chyba je
materiál, ne fatal"* doctrine napříč Phase 38.4 Krok 14b epoch.** ☕🌙
