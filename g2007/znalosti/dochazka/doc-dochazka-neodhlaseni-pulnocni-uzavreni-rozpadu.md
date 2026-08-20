# Zapomenutý odchod: půlnoční automat musí uzavřít i položky rozpadu; konec se nezobrazuje a řádek je červený

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se dělo špatně (nález Peťa 4.8.2026)

Půlnoční automat `att_auto_checkout_midnight` (g2007.python) uzavíral **jen hlavičku
docházky** (`tenant.att_entry`) na 23:59. **Položky rozpadu** (`tenant.vyroba_work`,
zakázka + činnost) nechával otevřené (`konec IS NULL`).

Otevřenou položku pak zavřel až **PŘÍŠTÍ PŘÍCHOD** toho člověka → vznikaly položky
přes půlnoc. Doložený případ: Pašek č. 29, 30. 7. 06:52 → 31. 7. 06:56 = **24,07 h**
na jedné položce, zatímco docházka téhož dne byla korektně uzavřená na 23:59.

Druhý, tišší důsledek: dokud položka zůstala otevřená, měla `hodiny = 0`, takže
**rozpad nesouhlasil s docházkou** (docházka 15,19 h × rozpad 0 h) a kontrola
rozpad × docházka to hlásila jako rozdíl.

## Oprava (4. 8. 2026)

1. **`att_auto_checkout_midnight` uzavírá i `vyroba_work`** — blok C, běží
   **až po commitu docházky**, aby případná chyba nezahodila už hotové odhlášení.
   Vylučuje položky navázané na `day_end` („Dnes už se mnou nepočítej").

2. **⚠️ POVINNÁ POJISTKA: jen DNEŠNÍ den.**
   `AND (w.od AT TIME ZONE 'Europe/Prague')::date = (now() AT TIME ZONE 'Europe/Prague')::date`
   Bez ní by automat při prvním běhu uzavřel **389 otevřených položek, z toho 353
   starých až do 2. 1. 2026** — tedy i v **zamčených měsících**. Zachytilo se to
   jen díky tomu, že se před ostrým během udělal dotaz „kolika položek by se to
   týkalo". **Tenhle krok nikdy nevynechávat.**

3. **Zobrazení: konec se u zapomenutého odchodu NEZOBRAZUJE.** 23:59 je dopočet
   automatu, ne skutečnost — ukazovat ho znamená tvářit se, že je to změřený čas.
   Místo něj je prázdno / „…" a **řádek svítí červeně**, ať se najde a opraví.
   - Docházka new: dataset `dochazka.zakazky_vse_list` vrací příznak `_neodhl`
     (poznámka obsahuje „auto-odhlášení", nebo konec padne na jiný den než začátek,
     nebo konec chybí u minulého dne); `CasKonec` je u nich NULL.
   - Opravy docházky: třída `neodhl` + štítek „⚠ neodhlášeno".

4. **Úklid července 2026** (nezamčený; zamčeno bylo 1–6/2026): 21 otevřených položek
   u 4 lidí (Pašek č. 2 ×12, Honomichl ×7, Novotná, Pillár) uzavřeno **podle konce
   v docházce**, ne natvrdo na 23:59 — aby rozpad seděl s docházkou. Doplnilo to
   **250,05 h**. Pozn.: těch 250 h je pořád automatův dopočet do 23:59 na OBOU
   stranách; skutečné časy odchodu musí doplnit mzdová účetní ručně (proto to
   svítí červeně). Poznámka na položkách: `[dopočet 4.8.2026: neodhlášeno, konec
   převzat z docházky]`.

## Co zbývá

Starší měsíce (leden–červen 2026) mají dál otevřené položky rozpadu. Jsou
v **zamčených** měsících — nesahat na ně bez rozhodnutí mzdové účetní.

## Poučení

- Když se opravuje automat, který píše do dat, **vždycky si nejdřív pusť dotaz
  „kolika řádků by se to týkalo"**. Tady to odhalilo záběr 389 řádků místo
  očekávaných pár dnešních.
- **Docházka je pravda pro mzdy** — když se dorovnává rozpad, přebírá se čas
  z `att_entry`, ne se dopočítává vlastní.
- Dopočtený čas se **nevydává za změřený**. Radši prázdno + červeně než číslo,
  kterému se dá uvěřit.

