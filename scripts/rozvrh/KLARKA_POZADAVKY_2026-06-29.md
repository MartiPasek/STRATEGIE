# Klárčiny nové požadavky k rozvrhu — e‑mail 28. 6. 2026 22:32

Zdroj: e‑mail Klára Vlková <vlkova@nerudovka.cz>, předmět „Rozvrh". Klárka prošla
poslední variantu (A, verze 4, 144/148) a poslala konkrétní opravy. Bez nich rozvrh
nemůže použít ani jako výchozí. Tohle jsou **tvrdá omezení (hard constraints)**.

## Třídy
**K1. Pátek — Ateliéry: žádná třída ne jen 3 h výuky, ale min. 6–7 h.** (např. 1. GD)
   → enc: pro každou třídu, pokud má v pá v Ateliérech >0 h, pak součet h v pá ≥ 6.
   (tj. zakázat „osamocená 3h dílna" v pátek — buď 0, nebo ≥6.)

## Per učitel — počet dnů výuky (distinct dny)
**K2. Beran — výuka ve 4 dnech** (teď 5). → `count(distinct den s výukou) == 4`.
**K3. Němejc — výuka ve všech 5 dnech.** → `== 5`.
**K4. Rešl — výuka ve 2 dnech.** → `== 2`.
**K5. Stichenwirthová — jen 1 den (st NEBO čt, ne oba).** → `== 1` a jen z {st,čt}.
**K6. Švehlová — jen 3 dny** (teď 4). → `== 3`. (drží Po/St/Čt dle screenshotu z 22.6.)

## Per učitel — krátké dny / okna
**K7. OBECNÉ PRAVIDLO (všichni učitelé): aspoň JEDEN den musí končit dřív** (ne každý den do večera = vopruz). Marti 29.6.: „dělat každý den do večera je vopruz, měl by končit aspoň jeden den dříve." Beran teď má všechny dny dlouhé (do 10. h) → musí mít aspoň 1 den kratší.
   → enc: pro každého učitele aspoň 1 vyučovací den, kde poslední hodina ≤ ~6. perioda (kratší/ranní den). Práh „dříve" doladit (návrh: poslední perioda ≤ 6).
**K8. Radová — max 1 den s velkým oknem (6h dírou) mezi výukou.** Teď má út i st.
   → enc: počet dnů, kde má díru ≥ ~6 h mezi bloky, ≤ 1.
**K9. Sadská — DGD do dopoledních hodin, ať má jen 1 odpolední výuku.**
   → enc: DGD bloky Sadské preferenčně/hard do dopoledne; max 1 den s odpolední výukou.

## Bloky / návaznost
**K10. Kuchtová — VP má mít DVĚ trojhodinovky** (teď jen jednu; chybí 2. půlka VP).
**K11. Lišková Lenka — Te NEMUSÍ po sobě** (uvolnění — každá hodina může zvlášť);
   **DIN ne 6 h v kuse, ale 2×3 h týdně** (rozdělit na dva 3h bloky v různých dnech).

## Stav zakódování
- [ ] K1 pátek Ateliéry ≥6
- [ ] K2 Beran 4 dny  · [ ] K3 Němejc 5 dnů · [ ] K4 Rešl 2 dny · [ ] K5 Stichenwirthová 1 den (st/čt) · [ ] K6 Švehlová 3 dny
- [ ] K7 ne všechny dny do 10h (obecné, vč. Pejřimovská) — UPŘESNIT
- [ ] K8 Radová max 1 den s 6h dírou
- [ ] K9 Sadská DGD dopoledne, max 1 odpolední
- [ ] K10 Kuchtová 2× trojhodinovka VP
- [ ] K11 Lišková: Te volně + DIN 2×3h (ne 6h blok)

Pozn.: K2/K6 jsou zpřísnění (teď má víc dnů) — solver to musí umět při zachování
úvazků. K7 a K8 jsou „anti‑krátký‑den / anti‑díra" pravidla na úrovni učitele.
Navazuje na `docs/nerudovka_rozvrh_kriteria.md` (33 kritérií) + tento delta.

---

## Odpovědi od Klárky (e‑mail 29. 6. 2026 17:08 + 17:17) — ZÁVAZNÉ

1. **Učebny 4. ročníku: JSOU ve stejném dokumentu** jako 1.–3. ročník (Google Doc
   `18pJ-ayufMn6oJM6gpxWH1N69sZregwSzp_JOoTFh3GI` + příloha `učebny pro předměty.pdf`).
   Ověřeno: `ucebny_doc.json` UŽ obsahuje 4.GD (8) + 4.MI (15) a solver je přes
   `_lbl()` (1U→4.GD, 1W→4.MI) používá. → 4. ročník NEMÁ chybějící učebny; tlak na 1U
   byl od mého tvrdého K3, ne od učeben. (Klárka: „buď víc pozorný".)

2. **Němejc (UZS4C) MÁ plný úvazek 24 h** (+3 h navíc). V `raw_skup.txt` 7 jednotek,
   suma 48 h/14 dní = 24 h/týden — kompletní. → 5 dnů je PŘIROZENÉ. Můj „má málo hodin"
   byl OMYL. K3 = měkké rozprostření na 5 dnů, ne tvrdě ==1 každý den (dělalo regresi 125/148).

3. **Stichenwirthová: st NEBO čt, jedno které** — = moje K5, potvrzeno.

4. **NOVÁ FLEXIBILITA: odborné v ateliérech NEMUSÍ být celé dny.** Klidně dopoledne
   (do 3./4./5./6. h), pak 7. h volno a žáci přejedou do Nerudovky (TV/ON/chemie/EKO —
   Klárka si doplní). → uvolňuje rozvrh + podporuje K7. Učitelé nemusí pořád do 16:40.

### Stav zakódování (aktualizace 29.6.)
- [x] K5 Stichenwirthová 1 den (st/čt); K2 Beran 4 / K4 Rešl 2 / K6 Švehlová 3 (TLIMIT)
- [~] K3 Němejc 5 dnů — PŘEDĚLAT na měkké rozprostření (má 24 h)
- [ ] K7 ≥1 kratší den (využít novou flexibilitu) · K1 pátek ateliéry ≥6 · K8 Radová díra · K9 Sadská DGD dopoledne · K10 Kuchtová 2×VP · K11 Lišková DIN 2×3h
- [ ] Přegenerovat → ověřit → poslat Klárce
