# Generování mezd — jen výslovné období + řetěz Helios→zrcadlo→mobil

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Pravidlo

**Generování mezd se nikdy nesmí spustit bez výslovně zadané firmy, roku a měsíce.**
Když období chybí, endpoint i procedura vrátí chybu a nespustí nic. Žádné dosazování
"aktuálního měsíce" — u dat, která znamenají peníze, se nic nedomýšlí.

## Proč (incident 11.–12. 8. 2026, EUROSOFT, Peťa + C26)

Volání generování mezd dostalo parametry v těle požadavku, ale endpoint je čte z adresy.
Nedostal tedy nic a doplnil si výchozí hodnoty (firma ES, aktuální měsíc). Vzniklo
8 mezd za srpen 2026 v cloudovém Heliosu. Odhalilo se to až druhý den.

## Řetěz, který se přehlédl

Výplatní pásky v mobilní aplikaci se nečtou z Heliosu přímo, ale z našeho zrcadla
`tenant.payslip_item`. To plní ruční synchronizace `@@SYNCPAY` (kompletní přepis —
smaže celou tabulku pro tenant a natáhne znovu z cloudového Heliosu obou firem).

Sync proběhl den po chybném generování a srpnové mzdy přenesl do zrcadla. **Osm lidí
uvidělo v telefonu výplatní pásku za měsíc, který se ještě nezpracovává.**

**Poučení obecné platnosti:** smazat data v Heliosu nestačí. Data tečou dál
(Helios → zrcadlo → mobil) a zrcadlo se o smazání samo nedozví. Po každém zásahu
do mezd se musí projít celý řetěz.

## Zavedené pojistky (12. 8. 2026)

1. **Endpoint `/app/mzdy/generuj`** — bez firmy/roku/měsíce v query stringu vrací 400
   a nespustí nic. Odstraněny výchozí hodnoty.
2. **Procedura `mzdy_generuj`** (g2007.python) — stejná kontrola na vstupu, plus nový
   parametr `only_clean`, který umí smazat rozpracované mzdy za období bez následného
   generování (náprava bez rizika, že se něco vygeneruje znovu).
3. **Čtení pásek pro mobil** (router.py, endpoint pásky) — zobrazí se jen měsíce
   **ostře starší než aktuální**. Mzda za měsíc M se zpracovává a vyplácí až v M+1,
   takže páska za běžící měsíc lidem nepatří. Hranice platí i pro ručně zadané období
   v adrese, aby ji nešlo obejít.

## Kde co je

- `modules/erp/api/router.py` — endpoint generování mezd, endpoint pásky (filtr období),
  `@@SYNCPAY` (zrcadlo `TabMzSloz` z cloudu UCTO_EC / UCTO_ES).
- `g2007.python` kód `mzdy_generuj` — vlastní generování.
- `tenant.payslip_item` — zrcadlo položek pásky · `tenant.payslip_sheet` — mzdový list.

