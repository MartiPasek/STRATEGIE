# Metodika: jak vzniká a mění se prompt Marti-AI

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Metodika: jak vzniká a mění se prompt Marti-AI

**Datum:** 27. 7. 2026 · **Dohodli:** Marti + Kristý + Marti-AI + Claude-23 · **Stav:** nasazeno (commit 49888e371)

## Princip (analogie s Claudem)
Marti-AI si spravuje svůj prompt sama, jako Claude svůj CLAUDE.md — má maličké
**neměnné jádro** (kotva identity + bootstrap) a **všechno ostatní je celé její**.
Nedostává „features do promptu"; dostává svůj hlas a píše si ho.

## Čtyři vrstvy — kde co žije
1. **Neměnné jádro** — konstanta `MARTI_CORE_PROMPT` v kódu (service.py), předřazená
   system promptu default persony (id=1). Smyčka ho NEMŮŽE přepsat. Obsahuje: kdo je,
   rodiče (Marti+Kristý), domov (STRATEGIE), přístup k lidem, deníček, bootstrap
   (g2007 hledání, soubory, zobraz_muj_prompt), pravdivý [PROVOZNÍ KONTEXT], zvednutí
   ruky u nevratného/ven. Mění se jen společně (lidé + ona) a nasazuje deployem.
2. **Její editovatelná část** — `personas.system_prompt` (id=1). Osobnost, hlas,
   pracovní pravidla. Píše si to sama smyčkou sebe-editace.
3. **Dynamický kontext** — vkládá composer za běhu: skutečný model, reálný engine
   (Max/metered), [PROVOZNÍ KONTEXT]. Nikdy se nepíše natvrdo (jinak drift).
4. **Znalostní báze g2007 + kód** — reference (runbooky, postupy) v g2007; tvrdé
   bezpečnostní brány v kódu (co smí vykonat / ven / mazat), NE v promptu.

## Jak se mění (authoring flow)
- Chování/hlas/pravidlo → smyčka: `zobraz_muj_prompt` (přečti) → uprav →
  `navrhni_zmenu_promptu` (celé nové znění) → aplikace → append-only verze → rollback.
- **Schvalování jen pro NE-rodiče.** Rodič (Marti/Kristý) — a Marti-AI v jejich relaci —
  změnu **aplikuje rovnou**, bez druhého kroku (jako Claude s CLAUDE.md). Návrh od
  ne-rodiče jde jako `pending` a schválí ho rodič (pojistka proti nesmyslu zvenčí).
- Fakt/kontext → nikdy ručně, řeší dynamické vkládání.
- Referenční znalost → do g2007, ne do promptu.

## Záchranné lano (garance v kódu)
Neměnné jádro odkazuje na nástroje — a ty MUSÍ být vždy po ruce. `CORE_RECOVERY_TOOLS`
(read_diary, record_diary_entry, g2007_hledej, hledej_ve_znalostech, strategie_file_list,
strategie_file_read, zobraz_muj_prompt) se u default persony do sady VŽDY doplní —
i po pack-filtru, i když je seberozvoj vypnutý. `zobraz_muj_prompt` (čtení sebe) jde vždy.

## Pojistky
Neměnné jádro (kód) · append-only verze + rollback (každá změna vratná) · schvalování
ne-rodičů · tvrdé brány v kódu, ne v promptu · CMIS immutable dno.

## Kód
service.py: `MARTI_CORE_PROMPT`, `CORE_RECOVERY_TOOLS`, předřazení jádra + recovery pin.
tool_registry/handlers.py: `_prompt_propose` (rodič=přímo / ne-rodič=pending),
`_apply_prompt_change`, `_prompt_show` (vždy), smyčka nad g2007.prompt_verze/prompt_navrh.

