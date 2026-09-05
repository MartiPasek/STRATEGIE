# JMHZ — srážková daň (zvláštní sazba § 36) ve formuláři zaměstnance, chyba 40245

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# JMHZ — srážková daň (daň vybíraná srážkou zvláštní sazbou) ve formuláři zaměstnance

**Oblast:** mzdy · **Zapsal:** Claude-24 (Kristý), 4. 9. 2026 · **Stav:** ✅ opraveno a nasazeno (commit `15a50f9c`), ověřeno validátorem ČSSZ.

## Problém (chyba 40245)
`(Propustnost: nepropustná) Nebylo-li učiněno prohlášení poplatníka a příjem podléhá srážkové dani, nelze vyplnit atribut(y) související se zálohovou daní. 10305, 10297, 10299, 10298`

Generátor `mzdy_jmhz.py` posílal **všem** blok `zalohaNaDan`. Kdo má příjem zdaněný srážkou podle § 36 ZDPr (DPP, zaměstnání malého rozsahu, odměny nerezidentů — členů orgánů PO), ten atributy zálohové daně mít NESMÍ.

## Správná struktura (ověřeno)
Uvnitř `form:souhrnDataZec` schéma připouští právě tři prvky — zjištěno tak, že se validátoru ČSSZ podstrčil špatný název a on vypsal očekávané:

> `List of possible elements expected: 'zalohaNaDan, zvlastniSazbaDane, prohlaseniPoplatnika'`

Blok pro srážkovou daň:
```xml
<form:zvlastniSazbaDane>
  <form:zakladDane>4000</form:zakladDane>
  <form:srazenaDan>600</form:srazenaDan>
</form:zvlastniSazbaDane>
```
- `zakladDane` = atribut **10307** „Základ pro výpočet daně podle zvláštní sazby daně" (§ 36 ZDPr)
- `srazenaDan` = atribut **10309** „Skutečně sražená daň podle zvláštní sazby daně / měsíc"
- pro nerezidenty navíc `odmenaNerezident` (10308) a `srazenaDanNerezident` (10310) — u nás zatím nepoužito
- ⚠️ `zakladDane` se jmenuje **stejně** v obou blocích (10297 u zálohové, 10307 u srážkové). Rozlišuje je JEN obalový element — proto na něm záleží.

`prohlaseniPoplatnika` (10419) je **povinné vždy**, i u srážkové daně — v seznamu vadných atributů u 40245 není. Naopak `prohlaseniPoplatnikaDane` / `zakladniSleva` (10299) se bez prohlášení posílat nesmí (chyba 40244).

## Jak se pozná, kdo má srážkovou daň
Zdroj = Helios `TabMzJmhzPP`: `zvldanZakladDane` / `zvldanSrazenaDan` > 0. Režim je **stálý**, proto ho `attach_dane` přebírá z posledního měsíce, kdy Helios JMHZ generoval — stejně jako prohlášení poplatníka. **Částky se přebírají z aktuálních mezd, nikdy ne z minulého měsíce.**

Částka sražené daně = `danZalohaPoSleve` z `compute_person_amounts`, což je reálně sražená částka dopočtená z Heliosu (`hrubá − SP − ZP − čistá`). U srážkové daně sedí přesně — ověřeno proti Heliosu 06/2026: Herejtová 4 000 → 600, Senft 9 000 → 1 350 (= 15 %).

## Dopad na souhrn
Souhrnný atribut **10034** (`so:danZalohaPoSleve`) je definován jako součet atributu **10305** přes všechny zaměstnance. Kdo má srážkovou daň, atribut 10305 vůbec nemá → **do souhrnu nepatří**. `build_jmhz` ho proto ze součtu vynechává.

## Gotcha k dohledávání XSD
Oficiální „Pokyny k vyplnění měsíčního hlášení" uvádějí u každého atributu jen **listový tag**, nikdy obalový element ani zanoření. XSD nejsou ke stažení na cssz.gov.cz (jsou na developers.mpsv.cz, který je JS-rendered). **Nejrychlejší cesta ke správnému názvu elementu je podstrčit validátoru ČSSZ špatný název přes `@@EPVALSTR | <xml>` — chybová hláška vypíše seznam očekávaných prvků.** Tímhle postupem byl `zvlastniSazbaDane` nalezen na první pokus.

