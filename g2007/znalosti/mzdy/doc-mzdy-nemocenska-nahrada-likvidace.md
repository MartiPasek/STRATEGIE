# Nemocenská: náhradu (složka 213) vytvoří až akce Likvidace v Heliosu, nepočítá ji STRATEGIE

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Nemocenská — jak vznikne náhrada (složka 213)

**Ověřeno 10. 8. 2026** (Peťa + Claude-26) na dvou reálných případech, po konzultaci
s mzdovou účetní. Do té doby to nikdo nevěděl, protože všechny starší nemoci byly buď
migrované ze staré Centrály, nebo tak krátké, že se nic nevyplácelo.

## Dělba práce

- **STRATEGIE posílá jen DNY A HODINY** — složka **200 Nemocenská - docházka**, částka 0.
  Slouží k tomu, aby Helios správně zkrátil základní mzdu.
- **Peníze počítá HELIOS** — složka **213 Nemocenská - náhrada**.
  **Ale ne automaticky** — vznikne až akcí **Likvidace**.

Do předzpracování složka 213 NIKDY nepatří — ani ji tam nehledej. Vzniká rovnou ve výpočtu mzdy.

## Postup krok za krokem

1. **Evidence DNP → Nový** → vybrat zaměstnance → **Přenos**
2. Vyplnit **Druh dávky = Nemoc**, **číslo rozhodnutí** z neschopenky, **Začátek**, hodiny 0.
   **Konec nechat prázdný, pokud nemoc pokračuje.** „Trvání DNP (lístky na peníze)"
   a „Přechod NM → DNP" nechat prázdné — u fungujících případů jsou prázdné taky.
3. **DNP k proplacení** → potvrdit dotazy (i ten na neukončené dávky) → **Vlož všechny**.
   „Vlož označené" u nemoci přes víc dnů nefunguje.
   ⚠️ **Nejdřív musí být z předzpracování smazaná složka 200**, jinak to hlásí
   *„Zadaná nepřítomnost se překrývá s jinou"*.
4. **Přegenerovat mzdy** — složka 200 se vrátí (posílá ji STRATEGIE).
5. **Výpočet mzdy → zaměstnanec → poklikat na složku 200 → Likvidace.**
6. Zkontrolovat částku, doplnit číslo rozhodnutí, **OK**.

Vznikne složka 213 s částkou. Stav dávky v evidenci bude „Přeneseno (část.)", pokud nemoc
pokračuje do dalšího měsíce — to je správně, likvidace se pak udělá znovu za další měsíc.
Datum „do" v okně likvidace je **konec měsíce**, ne konec nemoci.

## ⚠️ Pásmo 1 a Pásmo 2 NEJSOU karenční doba

V okně likvidace jsou pole „1. den", „Pásmo 1", „Pásmo 2" — jsou to **redukční pásma
průměrného výdělku**, ne rozdělení na placené/neplacené dny. **Náhrada náleží i za první
tři dny.** Ověřeno: zaměstnanec se 2 dny nemoci měl všech 16 hodin v Pásmu 1 a dostal
1 639 Kč. Kdyby to byla karence, měl by nulu.

Zákonná karenční doba (obnovená od 1. 1. 2025) se v tomto nastavení neuplatňuje —
potvrdila mzdová účetní i chování Heliosu.

## Kontrolní příklady (červenec 2026)

| dny / hodiny | PHV | náhrada 213 |
|---|---|---|
| 2 dny / 16 h | 189,60 | 1 639 Kč |
| 8 dnů / 64 h | 185,64 | 6 416 Kč |
| 3 dny / 24 h (pracovní úraz, červen) | — | 2 666 Kč |

## Co NEDĚLAT

- **Nezadávat náhradu ručně do předzpracování** — nepatří tam a Helios ji stejně přepíše.
- **Nepřeklápět hodiny mezi pásmy** — jsou to redukční pásma, ne dny.
- **Nespoléhat, že se náhrada dopočítá sama** po přenesení DNP. Nedopočítá.
  Bez Likvidace zůstane u nemoci nula a nikdo si toho nemusí všimnout.

