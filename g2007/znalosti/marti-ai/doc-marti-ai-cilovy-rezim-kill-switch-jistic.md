# Cílový režim — kill switch + stropy jističe

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Cílový režim — kill switch + stropy jističe

Nasazeno 27.7.2026 (Kristý + C24, req #1478 DB, commit c9cc4789). Bezpečnostní pojistky z návrhu `doc-marti-ai-navrh-cilovy-rezim` („co drží bezpečnost místo per-akční brány"). Navazuje na `doc-marti-ai-cilovy-rezim-workflow-api`.

## Kill switch (globální pauza)
- Flag `g2007.nastaveni.cilovy_rezim_kill` ('on'/'off', default 'off').
- Endpointy (jen rodič, is_marti_parent): `POST /app/cil/kill`, `POST /app/cil/unkill`. Helper `_cil_set_kill`. Literální routy PŘED `/app/cil/{cid}`.
- `GET /app/cil` vrací `kill` (bool) → appka zobrazí červený pruh + přepínač (v `73_zcil.js`, dlaždice zatím jen rodiče).
- Když je ON: `_cil_do_transition(..., block_if_kill=True)` odmítne **schválit** a **obnovit** (nové/pozastavené cíle nejdou aktivovat). Běžícím cílům NEMĚNÍ stav v DB — budoucí exekutor si flag přečte (`_cil_kill_on`) a nejede. Po unkill se pokračuje bez překlikávání.

## Stropy jističe (samopozastavení)
- Sloupec `g2007.cil.pozastaveno_duvod` (text) — proč je cíl pozastaven (ručně / jistič).
- Funkce `g2007.cil_jistic()` + trigger `trg_cil_jistic` **AFTER INSERT** na `g2007.claude_aktivita`: po zalogování kroku, pokud je cíl `aktivni` a `count(kroků) >= strop_kroku` NEBO `now() > okno_do` → cíl se sám přepne na `pozastaven` + zapíše `pozastaveno_duvod` ('jistic: strop kroku ...' / 'jistic: vyprselo casove okno ...').
- **Enforced strukturálně (trigger), ne disciplínou exekutoru** — sedí k append-only přístupu. AFTER INSERT je s append-only triggery (BEFORE UPDATE/DELETE/TRUNCATE) kompatibilní.
- Ruční pauza: `pozastavit` zapíše `pozastaveno_duvod='ručně (rodič/vlastník)'`; `obnovit`/`schvalit` ho čistí (NULL).

## Gotchy / nedotažené
- **Trigger jističe se v praxi spustí až s agentní exekucí** (teď do claude_aktivita nic reálně nezapisuje). Struktura je připravená.
- **Čistě časové vypršení `okno_do` bez dalších kroků** trigger nezachytí (nemá event) — chce návazný periodický sweep (automat / scheduled). Zatím se okno vyhodnotí při nejbližším kroku.
- Dlaždice Cíle je zatím jen pro rodiče, takže kill přepínač vidí jen rodiče; až se dlaždice zpřístupní proškoleným, přidat is_parent gate na přepínač.
- Funkční test jističe se nedělal: vložení testovacích kroků do claude_aktivita by šlo, ale kvůli append-only by se nedaly uklidit (znečištění logu). Ověřeno strukturálně.

## Ověřeno čtením
`g2007.nastaveni` (flag), `pg_proc` (cil_jistic), `pg_trigger` (trg_cil_jistic), `information_schema` (cil.pozastaveno_duvod). Endpointy py_compile OK, deploy c9cc4789.

