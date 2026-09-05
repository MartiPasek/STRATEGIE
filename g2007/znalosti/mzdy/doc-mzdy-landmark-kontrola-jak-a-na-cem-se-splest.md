# Landmark: jak ho zkontrolovat nezávisle a tři pasti, do kterých jsem spadl (4. 9. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Kontrola Landmarku — postup a pasti

**Peťa + C26, 4. 9. 2026**, při kontrole srpnových mezd. Přepočet dal 46 z 48 lidí na korunu;
oba rozdíly byly chybou kontroly, ne mzdy.

## Postup, který sedí

Volat `lm_engine` (g2007.python) s těmito vstupy — přesně jak je skládá `mzdy_benefity_apply`:

| vstup | odkud |
|---|---|
| `fond` | denní úvazek × pracovní dny měsíce z `firemni_kalendar` |
| `odprac` | `fond` − absence (`att_day_summary`: dovolená + lékař + nemoc + OČR + mateřská) |
| `dny` | `odprac / denní úvazek` — bez zaokrouhlení |
| `obl_sazba` | kancelář 109, dílna 279; 0 když má člověk v `benefit_volba` vypnuté OBL |
| `ho_hod_narok` | 6 × denní úvazek, jen když má nárok na HO |
| `osoh` | součet `wage_component.amount_real` složek mapovaných na Helios 432, **jen `krati_dochazkou = false`** |

⚠️ **`amount_real`, ne `amount_planned`.** Plánovaná částka z Podmínek dá jiný výsledek.

## Past 1 — složku 4320 nepočítáme my

Na výplatnici je řádek **„Korekce Landmark (srážka os. ohodnocení)", složka 4320.
Ta je Heliosova, my ji neposíláme.** My posíláme jedno číslo: složku 432 ve výši
`osobní ohodnocení + korekce`. Helios ji pak ještě krátí odpracovanou dobou.

Porovnávat vlastní korekci proti 4320 je tedy chyba. U některých lidí se ta čísla shodou
okolností rovnají (Zeman 40: obojí −4 349), u jiných vůbec (Bernardová 475: moje −4 353,
na pásce −900) — a vypadá to jako nález, přitom mzda je správně.

**Správně se kontroluje proti složkám 794 (OBL) a 795 (HO)**, ty jdou z našeho výpočtu přímo,
a proti 432 přes poměr odpracované doby: `432 na pásce = (osoh + korekce) × odprac / fond`.
Ověřeno na Bernardové: (7 500 − 4 353) × 78,4/134,4 = **1 836 Kč**, přesně jak má na pásce.

## Past 2 — jen HPP a jen aktivní lidé

**Nárok na Landmark má jen HPP** (Peťa 4. 9. 2026: *„dohody mají výplatu, ale jdou DPP bez
Landmarku"*) — Herejtová a Senft jsou DPP a na pásce Landmark správně nemají.

A do kontroly **nesmí spadnout lidé, kteří už nepracují.** Seznam z `user_smlouva` je bez
filtru na aktivní poměr — 4. 9. mi tam vlezli Klíková (18), Hrdinka (429), Jungmann (531)
a Mudra (492), kteří na srpnové pásce vůbec nejsou. Nezpůsobilo to špatné číslo, protože
nemají odpracovaný den, ale seznam „chybí na pásce" byl zbytečně zmatečný.

## Past 3 — kdo nárok nemá, i když ho podle kódu má

**Pašek Marti (EC 2 / ES 41) nárok na Landmark nemá** (Peťa 4. 9. 2026), stejně jako Mózer (47)
a Vlková (361). Vlková a Veverková (42) vypadnou samy přes denní úvazek pod 6 h, jednatelé
přes chybějící osobní ohodnocení — **ale Paškovi 2 podle pravidel v `mzdy_benefity_apply`
vychází OBL 2 289 Kč, a na pásce má správně nulu.** Něco ho vyřazuje mimo ten skript.
Neověřeno kde; při příští kontrole ho neber jako nález.

## Souvisí

[[doc-mzdy-landmark-podklad-vypocet]] · [[doc-mzdy-pravidla]]

