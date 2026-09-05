# Období nemoci/OČR/lékaře do mezd se bere z dokladu, ne z pracovních dnů (Peťa 4.9.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Období nemoci do mezd se bere z dokladu, ne z pracovních dnů

> oblast: `mzdy` · zadala Peťa 4. 9. 2026, nasadil Claude-26
> **Tento zápis je nadřazený všemu, co o zdroji období tvrdí něco jiného.**

## Jak to vůbec vzniká (Peťa 4. 9. 2026)
*„Nemoci, OČR a lístky se zadávají na základě dokladu ručně a zakládám je já nebo
Michelle, takže od lidí k tomu žádost není a nebude."*

Lidé o nemoc ani OČR nežádají. **Peťa nebo Michelle je opíšou z dokladu do Správy
docházky** a tím vznikne řádek v `tenant.att_absence_request` — není to žádost od
zaměstnance, je to **nosič toho, co se z dokladu opsalo**, včetně skutečného období.
Z něj se pak nagenerují denní záznamy, ale jen na **pracovní dny**.

## Pravidlo
- **Docházka new / denní záznamy** — jen **pracovní dny**. Tak to je a zůstává.
- **Mzdy (Helios)** — **skutečné období z dokladu**, včetně víkendových krajů.
  Helios z něj krátí základ (původní zadání Kristý 8. 7. 2026).

## Co bylo špatně
`mzdy_absence_rows`, blok (B) pro lékaře, OČR a nemocenskou, skládal `DatumOd`/`DatumDo`
**z denních záznamů**, tedy jen z pracovních dnů. Víkendy uvnitř období přeskočil správně,
ale **na krajích období usekl**. Doložené případy z roku 2026:

| Člověk | Na dokladu | Šlo do mezd |
|---|---|---|
| Vladimír Navrátil, nemoc | 1. 8. (**sobota**) – 10. 8. | 3. 8. – 10. 8. |
| Kristýna Marešová, OČR | 23. 6. – 28. 6. (**neděle**) | 23. 6. – 26. 6. |

Useknutý kraj = špatné krácení základu = špatná mzda. Nic nikde nehlásilo chybu.

## Oprava (4. 9. 2026, `mzdy_absence_rows`)
Dotaz vytahuje i `a.source_id` a přes něj `datum_od` / `datum_do` z toho, co se opsalo
z dokladu. Období se **ořízne na zúčtovací měsíc** (doklad může přecházet přes přelom,
mzdy se dělají po měsících). Jeden doklad = jeden řádek.

**Dvě pojistky, obě z reálného případu:**
1. **Zrušený nebo zamítnutý doklad se ignoruje** (`stav NOT IN ('cancelled','rejected')`).
2. **Den bez vazby jede po staru** — období se složí ze dnů přes víkendy.

## Proč je ta druhá pojistka důležitá — případ Trunec
Luboš Trunec měl nemoc opsanou 17. 8. – 28. 8. Peťa ji pak ve Správě **zrušila
a zkrátila na 26. 8.** Oprava založila nové denní záznamy, které už **vazbu na původní
doklad nemají**, a původní doklad zůstal ve stavu `cancelled`.

Do mezd tedy jde **17.–26. 8. složené ze dnů — a to je správně**, protože oprava je
novější pravda než původní doklad. Peťa 4. 9.: *„tak jak je Trunec, je to dobře."*

**Poučení: když se absence opraví v Opravách, vazba na doklad se ztratí a období se
napříště skládá ze dnů.** Není to vada — je to jediné rozumné chování, protože po
zkrácení už původní období neplatí. Ale je dobré o tom vědět, než to někdo bude
„opravovat".

## Neschopenky z ČSSZ
Peťa 4. 9. rozhodla, že se **nic dalšího nedělá** — doklad vždycky zakládá ona nebo
Michelle ručně, takže případ „nemoc bez opsaného dokladu" prakticky nenastává.

## Prověřeno, že tomu nic neodporuje
Prošla jsem aktivní záznamy G2007 o absencích ve mzdách a o období
(`doc-dochazka-absence-do-mezd`, `doc-dochazka-dovolena-navic-sickday-osvc-do-mezd`,
`doc-mzdy-nemocenska-nahrada-likvidace`, `doc-mzdy-zrcadlo-dochazky-ze-strategie`,
`doc-mzdy-pravidla`). **Žádný z nich zdroj období neurčuje**, takže není co zneplatňovat.
Jediné místo, kde to bylo popsané, byl komentář v kódu, a ten je opravený.

## Souvisi
[[doc-dochazka-absence-do-mezd]] · [[doc-dochazka-absence-bez-casu-krome-lekare]] ·
[[doc-mzdy-nemocenska-nahrada-likvidace]]

