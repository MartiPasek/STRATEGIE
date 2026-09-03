# Kaskáda rozpadu doplní činnost z předchozího úseku, už ji nepíše prázdnou (Peťa 3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Kaskáda rozpadu doplní činnost z předchozího úseku

> oblast: `dochazka` · zadala Peťa 3. 9. 2026, nasadil Claude-26

## Příznak
V přehledu „Docházka new" se objevovaly **minutové úseky (0,017 h) se zakázkou,
ale bez činnosti** — Lišková 3. 9., Honal, Brudnová, Egermaier a Voříšek 2. 9.,
Bláha a Lev 1. 9., Artim 28. 8. Vznikaly průběžně, každý den, a Peťa je v kontrole
neviděla, protože pravidlo `chybi_cinnost` ignoruje úseky do 0,1 h.

## Příčina (ověřeno v kódu)
`att_sync_vyroba_work`, krok 5 — „platný úsek bez pokrytí → prázdný řádek".
V INSERTu se `cinnost_id` psalo **natvrdo `NULL`**, protože píchnutí (`att_entry`)
činnost nenese; přebírala se jen zakázka.

Ta minutová okénka vznikají při **přepnutí zakázky za chodu**: od 20. 8. 2026 se
píchnutí při změně zakázky dělí na dvě navazující části
([[doc-dochazka-deleni-zaznamu-pri-prepnuti-zakazky]]), mezi nimi zbyde minuta,
kterou rozpad nepokrývá, a krok 5 ji zaplácne prázdným řádkem. Proto jsou přesně
1 minuta, mají zakázku a nemají činnost, a v datech se objeví až při běhu kaskády
(v noci nebo druhý den).

## Oprava (3. 9. 2026)
V INSERTu je místo `NULL` poddotaz — činnost se bere z **nejbližšího předchozího
aktivního úseku téhož člověka a dne**, který nějakou činnost má. Když žádný takový
není (první úsek dne), zůstane prázdno jako dosud. Peťa: *„udělej to podle ty co
tomu předcházela."* Ověřeno čtením na čtyřech reálných případech — poddotaz vrací
přesně ty činnosti, které jsme týž den doplnily ručně.

## Srovnaná data
9 řádků (8 minutových + Kristýna Marešová 1. 9. 13:36–14:30, která neměla ani
zakázku): činnost převzata z předchozího úseku, poznámka
„doplneno C26 3.9.2026 na pokyn Peti - prevzato z predchoziho useku tehoz dne".
Dřív téhož dne: 3 minutové úseky bez zakázky (Vápeník, Kolářová, Saad) dostaly
zakázku z předchozího úseku, a 5 úseků bez zakázky u lidí, kteří se nekontrolují
(Honomichl 4×, Marti 1×), bylo zneaktivněno.

## Co tím NENÍ vyřešeno
- **Práh 0,1 h** v pravidlech `chybi_zakazka` a `chybi_cinnost` zůstává — minutové
  úseky se pořád nehlásí. Peťa 3. 9.: *„musíme řešit i 0,01."*
- **Prvnímu úseku dne** se činnost převzít nedá — tam prázdno zůstane.
- Zdroj prázdných ZAKÁZEK je jiný a taky neopravený: potvrzení příchodu / návratu
  z pauzy přes notifikaci (`source = 'notif_confirm'`) a ohlášení z mobilu.

## Souvisí
[[doc-dochazka-deleni-zaznamu-pri-prepnuti-zakazky]] ·
[[doc-dochazka-prekryv-casu-blokuje-zezelenani-a-odbaveni-z-fronty]]

