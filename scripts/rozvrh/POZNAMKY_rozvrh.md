# Generátor rozvrhu Nerudovka — odborné GD/MI (stav 21.6.2026 noc)

## SYSTÉMOVÁ OPRAVA (hotová): reálné skupiny KOD_SKUP
- Dřív jsem si skupiny VYMÝŠLEL (G/I per řádek) → úvazky nesedly (Vlková 16h do 10h).
- Teď: lane = reálný KOD_SKUP z `ruvazky`. Jednotky = úvazek PŘESNĚ (POCET_HOD/2).
- Ověřeno: Vlková UNS6G cíl 16 = jednotky 16 = umístěno 16.
- WHOLE skup = skup předmětu 0P (ČJ) v třídě → blokuje všechny lanes (celá třída).
- LANES = ostatní KOD_SKUP v třídě (FW/FX, BF/BG, FY/FZ, D3-D6, EA/EB, KF/KG...).
- Slučování: Písmo(FR)+Typo(0D)→3h trojblok JEN když oba; ČJ 0P+0R→3h (jinak 1,5+1,5→2+2=4 chyba).

## UČEBNY (z PDF "učebny pro předměty" od Klárky, 1.-3. ročník)
- NENÍ pravda strop 2 učebny (IT2/MM). PG/animace/3D/web/foto smí do 5 PC učeben:
  IT2, MM, BŠ, BNA, BPG. + ateliéry BA,BK,BD1,BD4.
- rooms_of() v gen_core4.py přepsána přesně dle PDF.
- ⚠ 4. ROČNÍK (1U=4.GD + 4.MI) V PDF CHYBÍ → Klárka dodá. Teď hádám podle názvů.

## STAV placement
- Greedy (2E první): 74 %, Vlková 16 jistě.
- Globální solve: 83 %, Vlková ~14 (kolísá). FEASIBLE, ne optimum (gap ~5%).
- Zbytek neumístěno = obecná těsnost + nejistý 4. ročník.

## SPUŠTĚNÍ
- Greedy:  cat gen_core4.py drv_tail.py > g.py ; python3 g.py <seed> <variant> <perCls> <budget>
- Global:  cat gen_core4.py drv_glob.py > g.py ; python3 g.py <seed> <variant> <sec>
- Data: raw_skup.txt (trid|pred|skup|uk|hod), predmap.txt, gen_lang2_out.json, gen_tv_week.json
- ⚠ MOUNT TRUNCATION: skládej generátor v sandboxu (cat), needituj velký .py přes mount.

## ZÍTRA
1. Klárka dodá učebny 4. ročníku → doplnit do rooms_of.
2. Hybrid: 2E (Vlková) první greedy → zafixovat 16h → pak globální zbytek (Vlková 16 + max total).
3. Uložit variantu A do tenant.rozvrh_bunka (verze_id=4, tenant_id=13, blok='predmet').

## PRŮLOM 21.6. noc: zbandování jazyků → 98-99 %
- ROOT CAUSE placementu: jazyky se klíčovaly podle PŘESNÉ množiny tříd (cls,cj) → AJ 3.roč
  mělo 6 skupin s různým rozsahem spojených tříd → 6 bandů → rozsypané do 20+ slotů.
- FIX (gen_lang3.py): sloučit bandy přes UNION-FIND propojených komponent tříd (per cj+hod)
  → celý ročník dělá AJ ve stejný čas. 1W jazyky 26→8 slotů. 0 konfliktů.
- Učebny z PDF "učebny pro předměty" (1.-3.roč) v gen_core4 rooms_of: PG/animace/3D/web/foto
  do 5 PC učeben (IT2,MM,BŠ,BNA,BPG), ne 2!
- VÝSLEDEK: globální solve (cat gen_core5.py drv_glob.py) → 98-99 % úvazků, 0 konfliktů
  učitelů/učeben. variantaA_FINAL.json = nejlepší běh (zkontrolováno: 0 konfliktů).
- Zbývá: Švehlová ~3h na okraji (≤3 dny/20h velmi těsné).

## ZÍTRA (finální pass)
1. Klárka dodá učebny 4. ROČNÍKU = třídy 1U (4.GD) + 1W (4.MI) — v PDF nejsou, teď hádané.
2. Doplnit do rooms_of v gen_core4/5.
3. cp gen_lang3_out.json gen_lang2_out.json (banded jazyky jako vstup)
4. Spustit globální solve, vybrat nejlepší seed → variantaA_FINAL.json
5. PERSIST do tenant.rozvrh_bunka verze_id=4, tenant_id=13:
   - DELETE blok IN('jazyky','predmet')  (tv nech)
   - jazyky: řádek/spoj, trida=roll() spojené čárkou, kod_spoj, skup_zkr=zkr, kod_ucit, cj_uroven
   - predmet: trida=roll(trid), kod_skup=skup, skup_zkr=skup(kód skupiny pro split), pred=pnaz
     (viewer dělí podle zkr=skup_zkr, popisek z predzkr=join bakalari_pred_zkr na NAZEV; whole-class skup → skup_zkr='')
   - roll override jen {2E:1.GD, 2F:1.MI}; ostatní GD/MI sedí přes gen_lang2 CUR+1.
   - bakalari_pred_zkr má sloupce (nazev, zkratka) — join na NÁZEV ne kód!

## OPRAVA 22.6. 00:0x — DEN MÁ JEN 10 HODIN (ne 11!)
- Marti: rozvrh má 10 vyuč. hodin. NEextenduj na 11 (to bylo neplatné "100%").
- gen_core10.py = SPRÁVNÝ (cap 10). Švehlová PIN na Po/St/Čt (dny 1,3,4) — její reálný
  stálý rozvrh z Bakalářů (screenshot): Po 4,5,8,9,10 / St 1-6,8,9,10 / Čt 1,2,3,7,8,9 = 20h.
- Cap 10 + pin: Švehlová 17/20, celek 97%. Chybí jí 3h GDN ve 4.GD (1U).
- DŮVOD: 1U + 1W = 4. ROČNÍK, učebny HÁDANÉ (v PDF nejsou). Až Klárka dodá učebny
  4. ročníku → doplnit do rooms_of (gen_core10) → Švehlová dosedne na 20/20.
- Lunch NENÍ viník (test bez oběda taky 17). Je to room/alignment 4. ročníku.
- persist_A.sql byl vygenerován z 11h verze = NEPLATNÝ, přegenerovat po 4. ročníku.

## ZÍTRA finální (pořadí)
1. Klárka: učebny 4. ročníku (1U=4.GD, 1W=4.MI) → rooms_of v gen_core10.
2. cp gen_lang3_out.json gen_lang2_out.json
3. cat gen_core10.py drv_glob.py > g.py ; python3 g.py 0 A 38  (cílit 100%, Švehlová 20/20)
4. python3 gen_persist.py → persist_A.sql → bridge → banner.

## 22.6. odpoledne — varianty A/B/C/D LIVE + nová kritéria
- gen_core17.py = aktuální generátor. Nová tvrdá pravidla (mimo Švehlovou UXS9D):
  - max 1 přejezd mezi budovami za DEN (žáci i učitelé) — nF selektor + pairwise (žádný návrat do budovy).
  - max 7 h v kuse — učitelům přidána volná hodina v okně 4-7 (žáci to mají přes oběd → max 6 v kuse).
  - měkce: přejezd ≤2× týdně (penalta 20-60 na mixed-building dny).
- Švehlová (UXS9D) z těchto pravidel VYŇATA (marathonní středa, předměty nutně přes obě budovy).
- Persist: gen_persist_a.py = verze 4 (A, predmet-only, jazyky+TV nech). gen_persist_var.py V json = verze V (kopíruje jazyky+TV z verze 4 + odborné varianty).
- Pokrytí klesá s počtem tvrdých pravidel: A 95 %, B 94 %, C 90 %, D 95 %, vše 0 konfliktů. Zbytek = ruční doladění Klárkou (poslední míle).
- fw.claude_instance.instance_id je TEXT! public.users DELETE zakázán roli (jen INSERT/UPDATE).
