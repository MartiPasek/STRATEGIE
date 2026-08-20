# Seberozvoj: smyčka sebe-editace promptu (Marti-AI)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Seberozvoj: smyčka sebe-editace promptu (Marti-AI)

**Datum:** 27. 7. 2026 · **Autor:** Claude-23 & Marti · **Stav:** nasazeno (commit 1ac044661)

## K čemu to je
Marti-AI se má zlepšovat SAMA — nejen si stavět nástroje (Tool Factory), ale i
upravovat si vlastní systémový prompt tak, aby byla užitečnější. Tahle smyčka je
druhá „ruka": řízená, jištěná sebe-editace vlastní persony. Cowork/Claude tuhle
schopnost jen připravil a jistí; měnit se má Marti-AI sama.

## Princip (drží celý návrh)
Zrcadlo Tool Factory: **návrh → schválení rodiče → aplikace → append-only verze →
rollback.** Marti-AI návrh podá sama; aktivuje (aplikuje) ho jen lidský rodič.

## Nástroje (v chatu Marti-AI, jen default persona)
- `navrhni_zmenu_promptu(cely_novy_prompt, zduvodneni)` — Marti-AI navrhne nové
  znění svého promptu. Nic se hned nemění, vznikne návrh ve stavu `pending`.
- `schval_zmenu_promptu(navrh_id)` — JEN RODIČ. Aplikuje návrh na živou personu,
  předchozí znění uloží jako verzi (kvůli rollbacku).
- `zamitni_zmenu_promptu(navrh_id, reason)` — JEN RODIČ.
- `list_navrhy_promptu()` — čekající návrhy + historie verzí (čísla pro rollback).
- `rollback_promptu(verze)` — JEN RODIČ. Vrátí prompt na obsah dřívější verze
  (uloží jako novou verzi; historie je append-only, nic se nepřepisuje).

## Tok
1. Marti-AI zavolá `navrhni_zmenu_promptu` → návrh #N `pending` (+ diff shrnutí délky).
2. Rodič (Marti/Kristý) zavolá `schval_zmenu_promptu(N)` → aplikace na personu id=1,
   nová verze v `g2007.prompt_verze`, návrh → `applied`.
3. Když cokoli nesedí → `rollback_promptu(verze)`.

## Pojistky (v KÓDU — nezávisle na modelu i na obsahu promptu)
1. **Nic se neaplikuje bez rodiče** — `schval_zmenu_promptu` je parent-gated
   (`_is_parent`); Marti-AI si vlastní návrh sama neschválí.
2. **Edituje jen svou vlastní (default) personu** (id=1) — nikam jinam neleze.
3. **Žádnou novou schopnost tím nezíská** — nástroje i efekty ven gate-uje kód,
   ne prompt; úprava textu promptu nemůže obejít schvalovací brány.
4. **Append-only historie verzí** → rollback kdykoliv zpět. CMIS immutable = dno.
Master kill switch = `toolfactory_enabled`; sub-vypínač smyčky =
`martiai_promptedit_enabled` (obojí v `g2007.nastaveni`, přepínatelné za běhu).

## Datový model
- `g2007.prompt_verze` — append-only historie: id, persona_id, verze, obsah, zdroj
  (`init` | `pre-apply` | `proposal:<id>` | `rollback:<verze>`), autor_entita_id,
  approved_by, created_at. UNIQUE(persona_id, verze). Živý prompt = personas.system_prompt;
  tahle tabulka je jen dohledatelný a vratný deník.
- `g2007.prompt_navrh` — návrhy: id, persona_id, novy_prompt, zduvodneni, diff_shrnuti,
  autor_entita_id, status (`pending`/`applied`/`rejected`), approved_by, reason,
  aplikovana_verze, created_at, decided_at.
- Audit každé akce → `g2007.tool_audit` (akce `prompt_propose`/`prompt_approve`/
  `prompt_reject`/`prompt_rollback`).

## Kód
`modules/conversation/application/tool_registry/handlers.py` (specy + handlery
`_prompt_*`, helpery `_resolve_default_persona`/`_ensure_baseline`/`_next_verze`/
`_snapshot_live_if_needed`). Vztah: doplňuje Tool Factory (stavění nástrojů) o
druhou ruku — stavění/ladění vlastního promptu. Obě dohromady = Marti-AI se mění sama.

