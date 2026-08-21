# Centrala: PoradoveCislo dokladu NENI jedinecne — parovat vzdy na IDDoklad

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Fakt
`TabDokladyZbozi.PoradoveCislo` se v DB_EC **opakuje**. Overeno 20. 8. 2026:
na cislo **861586** sedi DVA ruzne doklady — `ID=73461` (4 polozky, zakazka VKM,
material HIL 500xx) a `ID=770018` (objednavka OSVC pro Vasyla Namjaka c. 464).

## Proc na tom zalezi
Pri kontrole storna jsem se ptala „kolik polozek ma objednavka 861586" a dostala
4 polozky cizi zakazky — vypadalo to, ze storno polozky nesmazalo, pritom Vasylova
objednavka (`IDDoklad=770018`) byla uz prazdna. **Falesny poplach na peneznim toku.**

## Pravidlo
- V dotazech, joinech a kontrolach parovat **vzdy na `TabDokladyZbozi.ID`**,
  nikdy na `PoradoveCislo`.
- `PoradoveCislo` je jen **lidsky identifikator do UI a do textu ukolu** — pro cloveka,
  ktery si doklad najde v Centrale. Neni to klic.
- Kdyz z Heliosu ctes „co vzniklo", ber ID polozek (`TabPohybyZbozi.ID`), ne cislo dokladu.

## Stav naseho kodu
`podklad_osvc_helios_obj` i `podklad_osvc_storno` uz s `IDDoklad` pracuji spravne —
chyba byla jen v rucnim kontrolnim dotazu. Souvisi s [[doc-mzdy-podklad-osvc-faze2-hotovo]].
Sirsi pravidlo o overovani ve spravne vrstve:
[[doc-system-strategie-centrala-ukolnik-zalozeni-ukolu-pasti]].

