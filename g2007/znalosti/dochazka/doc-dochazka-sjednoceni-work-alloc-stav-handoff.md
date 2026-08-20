# Sjednocení docházky na jednu tabulku vyroba_work — STAV + handoff (29.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> C24 (Kristý) 29. 7. 2026. Handoff soubor: `HANDOFF_dochazka_krok5-11_2026-07-29.md` (v kořeni repa).
> Souvisí: doc-dochazka-model-tabulky-dochazky, doc-dochazka-sync-absence-klasifikace.

## HOTOVO
- Kroky 1–4 + krok 5 DATOVÁ migrace: **749 řádků work_alloc → vyroba_work** (source_system='app'+source_id, ověřeno; režie→zakazka_ref='Rezie').
- Docházkový sync opraven (Fáze 1 nasazeno; Fáze 2 Volno 70/80/90 % typy hotové). `@@DOCHRESYNC <od> <do>` = wipe+reimport att_entry z Centrály.
- Zálohy: work_alloc_zaloha_2026-07-28.xlsx, dry-run Migrace_work_alloc_DRYRUN_2026-07-29.xlsx.
- ⚠️ prace_aktivni sloupec přidán a zase DROPnut (redundantní). Péťin počítaný PraceAktivni v data_setu zůstává. POZOR: `konec IS NULL` NENÍ spolehlivý „běží" — činnost 27 „Odměny fin.zakázek" má konec NULL a neběží (179 ks).

## ZBÝVÁ (večer 29.7.) — vše kód, deploy, TESTOVAT mobil (živé píchání!)
- Krok 5‑kód: přesměrovat zápisy → vyroba_work: mobil `_wa_open/_wa_close_running/_wa_running/_wa_latest_today` (~26530+), import `_dzt_process_parsed` (dochazka_zak_tab.py ~913), Opravy `att_fix_entry/add/merge` + `att_fix_day` čtení činnosti. vyroba_work nemá denorm názvy → dopočítat joinem / upravit mobil JS 60_dochazka.js.
- Krok 6: Makám/Čekám z vyroba_work (`app_work_today` ~26672); vyloučit činnost 27.
- Krok 7: zrušit fold `_sync_vyroba_work_app` (~27845) + volání (dochazka_zak_tab:1002, router 28093, 42956). `_sync_vyroba_work_ec` NECHAT.
- Krok 8: `_refresh_employee_active` (~48294) — odebrat mazání work_alloc.
- Krok 9: kontroly (subagent + Playwright mobil). Krok 10: DROP tenant.work_alloc (grep=0, koordinovat s Peťou data_set zakazky_vse_list fallback). Krok 11: update doc-dochazka-model-tabulky-dochazky na jednu tabulku.

Detailní čísla řádků a postup: viz handoff soubor.

