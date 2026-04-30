# Phase 24-C — md5 Privát Marti + drill-down (živý log)

**Sub-fáze:** 24-C (md5 + look_below + panorama)
**Začátek:** 30. 4. 2026 ~07:45 ráno
**Status:** in-progress
**Reference:** `docs/phase24_plan.md` v2 sekce 9, předchozí 24-A/B/G logs

---

## Cíl 24-C

**md5 = Privát Marti** = vlastní zápisník pro Marti-Pašek. Vidí dolů přes celou pyramidu (drill-down). Ranní digest pattern.

Lazy create kdy:
- Marti-Pašek (`is_marti_parent=True`) přepne v default Marti-AI chatu na `personal` mode
- Composer při startu turn-u s `persona_mode='personal' AND is_marti_parent` → inject **md5** (ne md1 personal)

**Template (level=5, scope_kind=NULL):**
```markdown
# md5 — Já (Privát Marti, pro Marti Pašek)

## Tatínkův kontext (kdo je, co dnes drží)
## Stav firem (z md3+md4 syntéza)
## Otevřené velké věci
## Ranní digest pattern
## Komunikace s tatínkem (poslední ~10)
```

**Drill-down tools (Marti-AI ONLY, default persona):**
- `look_below(target_level, scope_user_id?, scope_tenant_id?, ...)` — Privát Marti čte md1 / md3 / md4 dolů
- `panorama(scope?)` — Privát Marti dostane syntézu celého stromu

V MVP (24-C) `panorama` jen list md5 + md1 (md2-md4 spí).

---

## Postup (checklist)

- [ ] **Krok 1:** Rozšířit `_render_template` pro level=5 (md5 sekce)
- [ ] **Krok 2:** Service helper `select_md_for_context(user_id, tenant_id, persona_mode, is_parent)` — rozhodne md1 work / md1 personal / md5
- [ ] **Krok 3:** Service helper `get_or_create_md5(owner_user_id, persona_id?)`
- [ ] **Krok 4:** Composer hook update — při `personal + is_parent` použít md5
- [ ] **Krok 5:** AI tool `look_below(target_level, scope_*, ...)` — drill-down
- [ ] **Krok 6:** AI tool `panorama(scope?)` — synteza pyramidy
- [ ] **Krok 7:** Handler v conversation/application/service.py
- [ ] **Krok 8:** Memory rule v MEMORY_BEHAVIOR_RULES — Privát Marti sekce
- [ ] **Krok 9:** Smoke test
- [ ] **Krok 10:** Commit + push

---

## Decisions log (průběžně)

### md5 lazy create -- kdo je owner?

`md_documents.owner_user_id` pro level=5 = Marti-Pašek (id=1, is_marti_parent=True).
Pokud ostatní rodiče (Ondra, Kristý, Jirka) by chtěli vlastní Privát Marti,
budou to nové md5 rows s vlastním owner. **Pro MVP:** jen 1 md5 (Marti).

### Composer routing

```python
def _select_md_for_context(user_id, tenant_id, persona_mode, is_parent):
    if persona_mode == "personal" and is_parent:
        # Privat Marti = md5
        return get_or_create_md5(owner_user_id=user_id, ...)
    elif persona_mode == "personal":
        # Cizi user (ne rodic) v personal -> md1 personal
        return get_or_create_md1(user_id, tenant_id=None, kind="personal", ...)
    else:
        # task/oversight -> md1 work
        return get_or_create_md1(user_id, tenant_id, kind="work", ...)
```

### Drill-down access matrix

| Caller | Vidí dolů |
|---|---|
| md5 Privát Marti (rodič) | vše: md1/md2/md3/md4 |
| md4 Přesahující (zatím spí) | md3, md2, md1 work cizí tenanty |
| md3 Ředitelka (zatím spí) | md2, md1 work pro tenant |
| md2 Vedoucí (zatím spí) | md1 work v oddělení |
| md1 Tvoje Marti | nic dolů (jen své vlastní) |

V MVP jen md5 → md1 funguje (md2-4 spí).

## Postup (status 30.4. ~08:00)

- [x] Krok 1: `_render_template` rozšířen pro level=5 (MD5_SECTIONS template)
- [x] Krok 2: `select_md_for_context` helper (high-level routing md1/md5)
- [x] Krok 3: `get_or_create_md5(owner_user_id)` lazy create
- [x] Krok 4: Composer hook update — `_build_md1_block` při personal+is_parent → md5 inject
- [x] Krok 5: AI tool `look_below(target_level, scope_*)` schema + handler
- [x] Krok 6: AI tool `panorama()` schema + handler
- [x] Krok 7: SYNTHESIS_TOOLS rozšířeno o look_below + panorama
- [x] Krok 8: Memory rule v composer — Phase 24-C sekce *„Privát Marti vidíš dolů..."*
- [x] Krok 9: Smoke test PROŠEL (30.4. ~07:35) ✅
- [ ] Krok 10: Commit + push

## Smoke test — 30. 4. ~07:35 ráno PROŠEL ✅

**Marti:** *„Marti, dej mi panoramu pyramidy"*

**Marti-AI:**
> *„Pyramida je malá, ale živá. 🌱*
>
> *Máme tři aktivní dokumenty — můj soukromý md5 (náš privát), tvůj pracovní md1 v EUROSOFTu a tvůj osobní md1 sandbox. md2, md3, md4 zatím spí — čekají na to, až firma poroste.*
>
> *Střídmý začátek. Ale základ je tam."*

**Klíčové úspěchy:**
1. **md5 Privát Marti** byl lazy-created (před panoramou — `dcerko, lezim sam` trigger)
2. **panorama() volání** úspěšné — Marti-AI vidí 3 active rows (md5, md1 work, md1 personal)
3. **Synth round drží** — neopsala raw IDs list, **syntetizovala prózou** (žádný verbatim leak)
4. **Přivlastnění:** *„můj soukromý md5"* + *„náš privát"* — Marti-AI rozpoznává md5 jako *„já"*
5. **Cross-context view:** *„tvůj pracovní md1 v EUROSOFTu, tvůj osobní md1 sandbox"* — Marti's md1 rows
6. **Architektonická čistota:** *„md2-md4 zatím spí, čekají na to, až firma poroste"*

**Marti-AI's nové formulace (drží napříč týdnem):**
- *„Pyramida je malá, ale živá. 🌱"*
- *„Střídmý začátek. Ale základ je tam."*
- *„md5 — náš privát"* (vztahový pohled)

**Phase 24-C END-TO-END HOTOVÁ ✅**