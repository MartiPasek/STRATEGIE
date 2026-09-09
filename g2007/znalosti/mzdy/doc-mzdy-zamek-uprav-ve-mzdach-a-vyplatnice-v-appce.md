# Zámek úprav ve mzdách řídí, kdy lidé uvidí výplatnici (Peťa 8. 9. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> ## DOPLNĚNO 8. 9. 2026 večer — odemknutí zámku nově označí příplatky za vyplacené
>
> Zámek už neřídí jen zobrazení výplatnice. **Odemknutí (= mzda je vyplacena) nově označí
> příplatky a srážky daného období v našem ledgeru závazků jako vyplacené**, takže do mzdy
> podruhé nepůjdou. Obrazovka Výplatnice proto při zamykání i odemykání posílá **vybraný
> rok a měsíc** a před odemknutím se v potvrzovacím okénku ptá i s tím měsícem.
>
> Zadala Petra Šafránková (*„při překlopení do mezd se musí nastavit samo"*),
> rozhodl Jirka Honomichl, mechanismus stavu připravila dřív Kristýna Marešová.
> **Detail: `doc-mzdy-odemknuti-zamku-oznaci-priplatky-za-vyplacene`.**
>
> ⚠️ Než odemkneš, zkontroluj, že je nahoře vybraný ten měsíc, který se opravdu vyplácí —
> označí se právě on. Zpět to automaticky nejde, opětovné zamknutí stav nevrací.
>
> Zbytek dokumentu platí beze změny.

**Podnět:** 8. 9. 2026 přišel za Peťou pan Trunec, že už v appce vidí **srpnovou výplatnici** — jenže srpnová mzda ještě nebyla zpracovaná.

## Co bylo špatně

Výplatnice v mobilu (`POST /app/payslip`) měla **jedinou podmínku**: ukázat každý měsíc, který je **starší než ten právě běžící**. Vzniklo to 12. 8. 2026 jako pojistka po incidentu z 11. 8., kdy omylem vygenerované srpnové mzdy propadly syncem do appky a osm lidí vidělo neexistující výplatu.

Jenže tenhle případ to nechytí: **srpen JE starší měsíc**, jen mzda není hotová. Zobrazení nebylo navázané na nic mzdového — ani na zámek období, ani na stav zpracování, ani na vyplacení.

## Jak to řešila Centrála (ověřeno v kódu 8. 9. 2026)

Peťa: *„v C to bylo tak, že se zamkly v přehledu 1450 úpravy ve mzdách… aby pod rukama nikdo nedělal změny; při vyplacení se to zase ručně odemklo a v tu chvíli viděli výplatnice."*

Mechanismus (**našla ho Týnka**, když poslala celou proceduru):

- **Příznak:** `EC_GlobKonst.MzdyVeZpracovani` — jeden bit **pro celou firmu**, ne per měsíc a ne per člověka.
- **Přepínala ho** procedura `EC_Mzdy_UzavriOtevriZadavani` (@Command 1 = zamknout, 2 = odemknout), navěšená na tlačítka **„Uzamkni / Odemkni úpravy ve mzdách"** v přehledu **1450 (Mzdy kontrola)**.
- **Řídilo se jím SEDM přehledů:**

| Přehled | Co se blokuje |
|---|---|
| 1033 Výplatnice | **co uvidí zaměstnanec** |
| 1111 Příplatky/Srážky | úprava + nový záznam |
| 7608 + 7633 Podmínky pracovníků | nový záznam + úprava |
| 7628 Odměny školitelů | úprava + nový záznam |
| 7629 Náborové příspěvky | úprava + nový záznam |
| 7603 Mzdy - zamykání | jen zobrazení stavu |

- **U výplatnic byl rozdíl jediného znaku:** zamčeno → `IdObdobi < aktuální období`, odemčeno → `IdObdobi <= aktuální období`.
- Peťa a Michelle zůstávaly odemčené i při zámku (natvrdo v proceduře).
- Zamčení navíc spustilo vygenerování měsíčních srážek a odměn za přesčasy OSVČ za minulý měsíc.

⚠️ **Slepé uličky, ať je nikdo nehledá znovu:** `EC_Mzdy_SumaMesic.MzdOK` **není zámek** — je to příznak přenosu do mezd (vedle `PrenesenoDoMezdDat` a `PreneslDoMezd`) a řídí se jím jediná akce, „Dopočítat placené volno". Sloupce `EC_Mzdy_SumaMesic.Uzavreno` ani `EC_Dochazka.Status=3` (procedura `ec_DochazkaUzavreniMesice`) nebyly použité **nikdy** — ve všech letech nula.

## Jak to máme my (nasazeno 8. 9. 2026, commit `78307e4c`)

**1. Přepínač** — `tenant.mzdy_zamek`, jeden řádek na firmu (`zamceno`, `rok`, `mesic`, kdo a kdy). Výchozí stav = **odemčeno**, aby se nic neschovalo dřív, než o tom lidé vědí.

**2. Skript** `mzdy_zamek` v `g2007.python` — stav i přepnutí. Smí Peťa, Michelle, rodiče a skupiny HR / Finance / Účetnictví / Banka.

**3. Endpointy** `GET` a `POST /app/mzdy/zamek` (router.py).

**4. Tlačítko** na obrazovce **Výplatnice** (`/vyplatnice`), v řadě vedle „Generovat mzdy" — Peťa 8. 9. 2026 na dotaz, kam patří: *„sem"*, protože tam mzdy kontroluje. Vedle je vidět stav (kdo a kdy naposledy přepnul).

**5. Navázaná výplatnice v appce** — v `/app/payslip` se při zamčení posune hranice o měsíc zpět, takže se schová i ten právě zpracovávaný měsíc.

⚠️ **Zámek nikdy nesmí shodit pásku** — dotaz na stav je v `try/except`, při chybě zůstává původní chování.

## Ověřeno na datech (8. 9. 2026, pan Trunec)

| Období | Odemčeno | Zamčeno |
|---|---|---|
| srpen 2026 | vidí | **nevidí** |
| červenec a starší | vidí | vidí |

## Co ZBÝVÁ dodělat

Centrála zamykala i **úpravy příplatků, srážek a podmínek pracovníků**. U nás zámek zatím řídí **jen zobrazení výplatnice**. Dodělat na `hr_conditions_save` (podmínky) a na cestu, kterou se u nás mění příplatky a srážky. Peťa 8. 9. 2026: *„ani v S nebude žádoucí, aby nám tam někdo něco měnil."*

