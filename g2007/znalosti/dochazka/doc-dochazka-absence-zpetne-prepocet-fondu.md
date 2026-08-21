# Zpětně zadaná absence musí přepočítat doplnění do fondu — Správa docházky to jako jediná cesta nedělala

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Peťa + Claude‑26, 20. 8. 2026.** Nález na reálném případu (Saad Jarrar, 19. 8. 2026).

## Příznak

Zpětně dopíchnutá dovolená se v dni **nasčítala k už spočtenému doplnění do fondu**.
Saad Jarrar 19. 8. 2026 — práce 3,98 h + doplnění do fondu 4,02 h + dovolená 4,00 h
= **12,00 h za jeden den**. Peťa to poznala hned, den má mít osm.

## Příčina (ověřeno v datech i v kódu)

Automat (`g2007.python` kod `att_automat_level_day`) počítá doplnění do fondu
**jednou za noc** (`att_maybe_level_catchup`, jeden běh na den, okno 4 dny zpět).

- doplnění 4,02 h vzniklo o půlnoci, kdy dovolená ještě neexistovala (8,00 − 3,98),
- dovolenou zadala Peťa až ráno ze **Správy docházky**,
- a **ta cesta žádný přepočet nespouštěla**.

Přepočet po ručním zásahu (`_att_automat_recalc_day`, router.py = tenký delegate na
`att_automat_level_day` v cíleném režimu) volaly do té doby jen **Opravy docházky**
(`att_fix_entry`, `att_fix_add`, `att_fix_void`, `att_fix_merge`, `att_fix_polozka`,
`att_entry_trim`) a **nahlášení absence z mobilu** (`att_absence`, vlastní kopie bez
guardu). Modul Správy docházky (`modules/erp/api/dochazka_absence_sprava.py`, vznikl
30. 7. 2026) ho nikdy neměl — **nikdo ho neodstranil**, jen tam od začátku nebyl.

## Oprava (nasazeno, commit `d2d9ff6f`)

Nová funkce `_prepocti_fond(emp, dny)` v `dochazka_absence_sprava.py` volá **existující**
`_att_automat_recalc_day` — žádný nový výpočet se nepsal. Zapojená ve všech třech cestách.

- `/app/dochazka-abs/new` — dny nové absence,
- `/app/dochazka-abs/save` — staré dny (odkud absence zmizela) **i** nové,
- `/app/dochazka-abs/delete` — dny, ze kterých se absence rušila.

Nikdy nevyhodí výjimku — absence je v tu chvíli zapsaná a uložení nesmí spadnout kvůli dopočtu.
Dnešek si `_att_automat_recalc_day` ohlídá sám (nepřepočítává, dokud někomu běží směna).

## Jak má den s absencí vypadat (ať se to nehlásí jako chyba)

Do dne s absencí se **nedopichuje** — dopíchnout hodiny člověku na dovolené nedává smysl.
Absence se ale započítá do denního součtu, takže **odpis nad fond proběhnout musí**
(Peťa 4. 8. 2026, přímo v kódu automatu).

Saad 19. 8. po opravě = 3,98 h práce + 4,00 h dovolená = **7,98 h**, žádné doplnění.
Chybějících 0,02 h se nedopisuje — automat zapisuje až od rozdílu 0,1 h. Ověřeno
sdíleným výpočtem `tenant.att_den_hodiny(2, den, den)`.

## Pojistka

`absence-prepocita-doplneni-do-fondu` — hledá dny, kde absence vznikla **později** než
dopočet automatu a nikdo to už 36 hodin nesrovnal. Tolerance 36 hodin je schválně
(noční běh jede jednou denně a přepočítává 4 dny zpět, takže čerstvý rozdíl si srovná sám).

## Poučení

**Když tutéž věc jde udělat z víc obrazovek, přepočet patří ke KAŽDÉ z nich.**
Nová cesta si ho sama od sebe nepřinese a chyba je tichá — data vypadají platně,
jen jedno číslo je z doby před zásahem. Při hledání příčiny se proto ptej nejen
„počítá se to správně", ale i „**spouští to vůbec něco po TÉHLE cestě**".

Sourozenec staršího nálezu `doc-dochazka-automat-prepocet-guard-vlastni-radek`
(5. 8. 2026) — tam se přepočet volal, ale zevnitř se zablokoval; tady se nevolal vůbec.

