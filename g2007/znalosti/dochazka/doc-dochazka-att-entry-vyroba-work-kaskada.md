# Docházka FINÁLNÍ model: att_entry=hlavička, vyroba_work=položky + kanonická kaskáda (rozhodnutí Kristý+Marti 30.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> Rozhodnutí Kristý + Marti (člověk) 30.7.2026. NAHRAZUJE dřívější „zářijovou přestavbu / vyroba_work jako pohled"
> (to byl verdikt Marti-AI msg 11348/11360, zapsal C28) — Marti (člověk) rozhodl: **žádná přestavba, tohle je KONEČNÁ verze docházky.**

## Finální model (ZÁVAZNÝ, tabulky zůstávají)
- **tenant.att_entry = HLAVIČKA** — kdy/kolik/typ za den (časy, hodiny, typ, zakázka `project_ref`). PRAVDA pro mzdy.
  Drží i pauzy, konec dne, ABSENCE (dovolená/nemoc/lékař/OČR). Absence jdou odtud do mezd přes att_day_summary.
- **tenant.vyroba_work = POLOŽKY** — rozpad ODPRACOVANÉHO času na zakázku+činnost. Váže se na hlavičku přes `att_entry_id`.
  Drží JEN práci/režii/HO. **Absence do vyroba_work NEPATŘÍ** (ověřeno 30.7.: mzdy je berou z att_entry/att_day_summary,
  ne z vyroba_work; leak absencí do vyroba_work = regres, uklizen 30.7.).

## Dělené vlastnictví (proč ne „přegeneruj jednu z druhé")
- **Čas/hodiny/typ vlastní att_entry** (hlavička). Činnost vlastní vyroba_work (položky). Zakázka je na obou (drží se stejná).
- att_entry NEMÁ činnost → nejde z něj vyroba_work přegenerovat (ztratila by se činnost).
- vyroba_work nemá pauzy/absence → nejde z něj přegenerovat att_entry.
- Proto: NE „regenerace jedním směrem", ale **kaskáda „dorovnej a zachovej"**.

## Kanonická kaskáda `_att_sync_vyroba_work(s, employee_id, den)` — jedno místo pravdy
Volá ji KAŽDÁ cesta měnící docházku (oprava fix/entry|add|merge, storno, import, Makám). Algoritmus pro (člověk, den):
1. Vezmi PLATNÉ (`status<>superseded`) att_entry úseky typu work/overhead/homeoffice.
2. vyroba_work řádky dne, které NEpřekrývají žádný platný úsek → `is_active=false` (segment zanikl/sloučil se).
3. Řádky překrývající platný úsek → přiřaď `att_entry_id` toho úseku, **ořízni od/konec do segmentu**, přepočítej hodiny.
4. Duplicitní v rámci (úsek, zakázka, činnost) → nech jeden (span), ostatní `is_active=false`. (Řeší fragmentaci po sloučení.)
5. Platný úsek bez pokrytí → založ prázdný vyroba_work řádek (činnost NULL k doplnění).
**Činnost se kaskádou NIKDY nepřepisuje** — jen se dorovnávají časy a životní cyklus.

## Invarianty (hlídat)
- Časy položek ⊆ segment hlavičky (součet/rozsah sedí). Zakázka stejná na att_entry.project_ref i vyroba_work.zakazka_ref.
- Absence/pauza/konec dne → jen att_entry, nikdy vyroba_work.
- Vazba přes att_entry_id (ne přes shodu času) je nosná; časový match jen fallback.

## Stav 30.7.2026
Storno (`att_fix_void`) kaskádu do vyroba_work UŽ má (deactivate přes att_entry_id, minutový fallback). OPRAVA
(fix/entry|add|merge) má jen dílčí časové okno (moje krok-5) → má se nahradit touhle jednou funkcí. K implementaci:
dry-run na Petře 9.7. (att_entry HO 08:19-15:58 sloučeno, vyroba_work drží staré fragmenty → po kaskádě 1 řádek).
Souvisí [[doc-dochazka-model-tabulky-dochazky]], [[doc-dochazka-dochazka-new-skryva-dochazku]], [[doc-dochazka-doch-jeden-zdroj-co-se-nedela]].

