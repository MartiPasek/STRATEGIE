# Audit Klárčiných pravidel vs generátor odborných (23.6.2026)

Zdroj pravidel: `KLARKA_POZADAVKY_2026-06-22.md`. Generátor: `gen_odb3.py` (odborné only, DB busy).

## ✅ UŽ ZAKÓDOVÁNO (ověřeno proti kódům učitelů z bakalari_ucit)
- **Denní limity učitelů** (t_ok): Ždimerová UZS4U od 2.h · Šedová UOS6Q do 7.h ·
  Kubálková UI7OD St od 4.h · Layerová UYS9G Pá do 4.h · Hlaváč UMS61 Čt do 3.h ·
  Sylva Ježková UZSA4 volná středa · Vlková UNS6G mimo čtvrtek + od 2.h.
- **Počet dní učitele** (TLIMIT): Pejřimovská UTS88 ≤4 · Švehlová UXS9D ≤3 · Beran UOS6U ≤4 ·
  Rousová UZS4O ≤4 · Toušová UOS6X ≤3 · Rešl UVS8S ≤2 · Sadská UPS70 ≤3 · Kuchtová UUS8D ≤4.
- **Vlková ne stále do večera**: max 1 den s výukou 9.-10. h (default, Klárka 23.6.).
- Výuka do 10. h; pátek do 7. h; max 7 v kuse (polední okno ≤3); 1 přejezd budov/den;
  ne za sebou budovy; oběd; učebny per předmět (room_doc/rooms_of dle PDF); 3h ateliérové bloky;
  GUT 2h(2.GD)/3h(3.GD); MD 4.GD 3h / 3.GD 2h; Te 4.GD 2h; PT 3h.

## 🔧 DOPLNĚNO 23.6. (bylo mezera)
- **Tesliuk U0SAL jen pátek** (6h MD 4.GD) — PŘIDÁNO. *Současná LIVE verze (verze 4) to PORUŠUJE
  (MD 4.GD bylo v pondělí) — opraveno v gen_odb3, čeká na swap/final run.*
- **GDN názvy 5A/5B** (3.GD) → "Grafický design a navrhování" v predmap.

## ⏳ PENDING (soft/komplexní — rozhodnout s Klárkou, riziko infeasibility)
- **Max 6 OKEN (volných hodin mezi výukou) / učitel / týden** — vyžaduje gap-detekci v CP, neudělané.
- **Max 2 odpolední výuky nad 15:00 (h8-10) / učitel / týden** — modelovat jako soft (ateliér 3h bloky často běží pozdě → tvrdě by mohlo být infeasible).
- **Pejřimovská UTS88 volné Po/Pá** (konkrétní dny, ne jen ≤4 dní) — má riziko (12h+ GDN do 3 dnů).
- **Per-předmět učebny**: Te 4.GD → BA · GDN 4.roč jen BNA/BPG (teď i BŠ) · MD 4.GD proti WDMA (soft) ·
  Typografie+Písmo 1.GD do 14 h (≈ konec ≤7. h) · Te+PT 1.MI (Rousová) trojhodinovka [? upřesnit].
- **5F/5G ve 2.MI** = nezmapované kódy (ne v bakalari_pred) → Klárka potvrdí názvy.

## Spuštění
`python3 gen_odb3.py 0 A 45` → gen_odb_A_0.json → `python3 _verify.py A 0` (0 konfliktů) →
`python3 persist_odb.py A 0` → persist_v4_odb.sql → bridge (banner). DB busy: db_cbusy.txt + db_trbusy.txt
(z verze 4 jazyky+tv; přegenerovat při změně jazyků/TV dotazem na rozvrh_bunka).
