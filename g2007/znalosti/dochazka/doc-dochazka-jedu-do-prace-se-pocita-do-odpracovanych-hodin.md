# NALEZ - "Uz jedu do prace" (typ commute) se pocita do odpracovanych hodin a jde do mzdoveho podkladu (Peta 8.9.2026, ceka na rozhodnuti)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# NALEZ - "Uz jedu do prace" se pocita do mzdoveho podkladu

**Nasel Claude-26 na dotaz Peti 8. 9. 2026.** Peta: *"uz jedu do prace ma byt jen info"*.
**Zatim se NIC nezmenilo** - ceka se na rozhodnuti, protoze jde o penize a o sdileny vypocet.

## Co je overeno (cteno ze zdroju a z dat 8. 9. 2026)

1. Tlacitko **"Uz jedu do prace"** v mobilu zaklada v dochazce **skutecny zaznam typu
   `commute`** (Cesta) s casem od-do, zdroj `mobile_app`, poznamka "Jedu do prace - dorazim za N min".
2. Kanonicka funkce **`tenant.att_den_hodiny`** ma ve vyctu odpracovanych typu
   `c IN ('work','overhead','homeoffice','commute')` - **cestu tedy pocita mezi odpracovane**
   a sliva ji s praci do jednoho useku.
3. Tim se dostane do **`att_day_summary`** (mzdovy podklad, sloupec `cas_celkem`) a odtud
   dal - podklad ctou `mzdy_generuj`, `mzdy_loajalita_rows` (prescas nad fond do slozky 651)
   i `payroll_raporty`.
4. **Dolozene dopady** (fond cervenec 176 h, srpen 168 h - z `att_calendar_day`)
   - Lubos Trunec (Vyroba), cesta 29. 7. 05.27 az 05.51 = 0,41 h. FPD cervenec **177,33 h**,
     tedy 1,33 h nad fond; bez cesty by bylo 0,92 h.
   - Michal Jirkovsky (Vyroba), cesta 14. 8. 07.03 az 07.21 = 0,31 h. FPD srpen **168,13 h**,
     tedy 0,13 h nad fond; **bez cesty by byl 0,18 h POD fondem** a prescas by mu nevznikl vubec.
   - Oba jsou ve skupine Vyroba, kde se prescas nad fond proplaci.
5. Takovych zaznamu je v datech **sest** (cerven az srpen 2026, v zari zadny) a **zadny z nich
   neni sluzebni cesta** - vsechny vznikly timhle tlacitkem.

## Co se rozhoduje

- **(a) opravit u zdroje** - aby "uz jedu do prace" vubec nezakladalo dochazkovy zaznam,
  jen zpravu vedoucimu (stejne jako nemoc a OCR, viz `doc-dochazka-mobil-nemoc-ocr-lekar-jen-info-vedoucimu`);
- **(b) opravit ve vypoctu** - vyradit `commute` z odpracovanych typu v `att_den_hodiny`;
- **(c) zpetne** - jestli resit tech par desetin hodiny v uzavrenem cervenci a srpnu.

⚠️ `att_den_hodiny` je **sdileny vypocet** (mzdy, prehledy, nocni automat), takze pred
zasahem patri **dopadova mapa** - kdo ji plni, kdo ji cte, co zustane po staru
(pravidlo Peti, `doc-system-strategie-dopadova-mapa-sdilene-hodnoty`).

Souvisi: `doc-dochazka-opravy-jen-prace-cesta-pauza-absence-patri-do-spravy` (od 8. 9. 2026
uz Cesta nejde vybrat pri rucni oprave - to je jina vec a s timhle nalezem se neplete).

