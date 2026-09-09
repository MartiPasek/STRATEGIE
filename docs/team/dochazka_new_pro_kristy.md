# „Docházka NEW" — co řešíme, podklad pro Kristý

> Peťa + Claude‑26, 22. 7. 2026 večer. Ke konzultaci s Kristý (zítra).
> Souvisí: přehled `/dochazka-po-zakazkach`, doktrína **Docházka × Výroba separace**
> (Marti 13. 6.), `doc-dochazka-po-zakazkach-prehled`.

## Co Peťa chce
Přehled „Docházka po zakázkách" má ukazovat **docházku VŠECH lidí**, ne jen výrobní
práci na zakázkách. Konkrétně:

- **Výroba** → přes svoje **zakázky** (reálné VR… + Rezie).
- **Kancelář / ostatní** → jejich docházka jako zakázka **„Rezie"**.
- **Absence** (dovolená/nemoc/lékař) jako dosud.
- Data **z Centrály i z app**, za **zvolené období** (např. červenec).
- **Editace dvojklikem** (formulář jako v Centrále).
- Přejmenovat uzel na **„Docházka NEW"** (prosté „Docházka" už nejspíš někde je).

Rozhodnutí Peti k dvojímu počítání: **„výroba přes zakázky, ostatní jako Rezie,
každý započítaný jednou, žádné dvojí hodiny."**

## Co je hotové a nasazené (22. 7.)
- Přehled `/dochazka-po-zakazkach`: **editace dvojklikem**, formulář **přesně jako
  Centrála** (bez „NOVÝ ZÁZNAM"; Blbost a Rezie pole Peťa vyhodila). Ukládá do
  `tenant.vyroba_work`: zakázka, činnost, od, konec, hodiny, poznámka.
- **Absence a centrálské řádky** se otevřou jen ke čtení (zatím). Pauza / Vedoucí
  poznámka / zaškrtávátka (Požadavek úpravy, Vedoucí schváleno) se **jen zobrazují** —
  nemají zatím v DB místo, dodělá se.
- Skrytá pole v přehledu (id, druh řádku, surové hodnoty) pro předvyplnění formuláře;
  endpointy `…/cinnosti` a `…/save`.
- Klik/dvojklik zrychlen (výběr řádku se obarvuje inkrementálně, ne překreslením 14k řádků).

## Jádro problému
**Docházka × Výroba separace** (Marti 13. 6.): `att_entry` = čas a přítomnost
(příchod/odchod/pauza/absence, **BEZ zakázky**), `vyroba_work` = **zakázka × činnost**.
Kancelář **nemá `vyroba_work`** — jejich odpracovaný čas je v `att_entry` (presence).
Přehled ale z `att_entry` tahá **jen absence, ne přítomnost** → kancelář vidí jen dovolené.

## Data (ověřeno 22. 7.)
- `vyroba_work`: **14,7 tis. řádků**, **42 lidí** (app+centrala1) — jen výrobní práce.
  Kancelář/režie **0**.
- **Petra** (user 18, osobní číslo 1): **0** `vyroba_work`; **6** absencí; ale **514**
  `att_entry`. Za **červenec 2026 v app**: presence/work 23 zázn. / **131 h**,
  homeoffice 7,7 h, nenárokova 24,5 h, fond_doplnění 5,8 h, day_end 18×. → **Má
  napíchané, přehled to nezobrazuje.**
- **Centrála `EC_Dochazka`**: jedna sjednocená tabulka, **401 tis. řádků** (138 tis.
  Rezie), **62 tis. od 2025**, **78 lidí**. Petra tam má **4 665 řádků, VŠE Rezie**.
  Sloupce sedí na formulář: `CisloZakazky`, `DruhCinnosti`, `CasZacatek/Konec`,
  `CasPauza/Blbost/Rezie`, `ZamPoznamka`, `VedPoznamka`, `VedSchvaleno`, `PozadPomocVed`…
- **Import Centrála → `vyroba_work` vynechal režijní/kancelářské řádky** (proto kancelář 0).

## Dvě tvrdá omezení
1. **Zdroj režijních dat.** „Docházka všech včetně Rezie" musíme odněkud vzít — režie
   je v Centrále (`EC_Dochazka`), u nás jen částečně (app `att_entry` presence, jen app éra).
2. **Výkon.** Nejde renderovat statisíce řádků — přehled **zamrzá už u 14 tis.**
   Nutný **filtr období** (po měsíci).

## Otevřené otázky pro Kristý
1. **Odkud brát režii/kancelář?**
   a) číst přímo z Centrály `EC_Dochazka` za období (věrné, hned, ale read‑only a cross‑DB),
   b) doimportovat do `vyroba_work` (velká migrace ~138 tis., zásah do importu — Martiho oblast),
   c) skládat z app `att_entry` presence (jen app éra, historie z Centrály chybí).
2. **Červenec z app:** Petra má 131 h work + další presence napíchané v app — jak je
   zobrazit jako Rezie? ⚠️ presence **není prostý součet** — kategorie „nenárokova"
   běží **souběžně** se směnou (dvojí počítání, viz doktrína); brát správné kategorie /
   hodiny ze serveru.
3. **Filtr období** — default aktuální měsíc? Picker měsíce?
4. **Editovatelnost:** app řádky editovat u nás; Centrála read‑only (opravit v Centrále,
   nebo write‑through později přes MCP).
5. **Dvojí počítání app × výroba:** přítomnost jako Rezie jen tam, kde **není**
   `vyroba_work` (per člověk‑den) + jen správné presence kategorie.
6. **Přejmenování** uzlu 189 na **„Docházka NEW"**.

## Návrh Claude‑26 (k diskusi)
Přehled **bounded na měsíc**; UNION: `vyroba_work` (editovatelné) + absence + přítomnost
jako **Rezie** — pro app éru z `att_entry` presence (správné kategorie, jen dny bez
`vyroba_work`), pro historii z Centrály `EC_Dochazka` read‑only. Rozhodnout, jestli
Centrálu číst přímo, nebo doimportovat.
