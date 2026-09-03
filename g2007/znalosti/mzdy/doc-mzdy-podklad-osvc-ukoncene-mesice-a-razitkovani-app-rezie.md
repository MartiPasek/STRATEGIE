# Podklad OSVČ: jen ukončené měsíce + razítkování odfakturované app režie

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Kontext
Podklad fakturace OSVČ (`g2007.python` `podklad_vyplaceni_pdf`, LIVE) měl u dílenských OSVČ dvě odchylky proti realitě dílny (Dušanův přehled). Obojí vyřešeno 3.9.2026 (C24, Kristý).

## 1) Počítat jen UKONČENÉ měsíce (verze 11)
Podklad bral režii/dovolenou/zakázky až do `today()`, takže do částky tekl i rozpracovaný běžící měsíc → nesedělo s dílnou. Fix: horní datová mez `do_d` = **poslední den předchozího měsíce** (`today().replace(day=1) - timedelta(days=1)`), místo `today()`. Období i `m_start` se počítají z `do_d`. Důsledek: kluci dostanou fakturu od poslední fakturace do konce posledního ukončeného měsíce (např. k 3.9. => do 31.8.).

## 2) Razítkování odfakturované APP režie (bod 1)
Historická díra: app režie (`vyroba_work.source_system='app'`, `zakazka_ref ILIKE 're%ie'`) se v Centrále fakturovala přes Dušanovo generování, které razítkuje jen docházku (IDPolVObj v Centrále), NIKOLIV `vyroba_work`. Proto app režie, co JIŽ byla odfakturovaná, zůstala `fakturace_obj_id IS NULL` a podklad ji počítal znovu. Příklad Voříšek (327): červen zůstal nefakturovaný, ač objednávka 1.7. ho pokryla.

**Pravidlo (potvrdila Kristý):** app režie s datem **před 1. dnem měsíce POSLEDNÍ režijní objednávky** té osoby (`MAX(EC_Zakazky_PlatbyZam.DatumPorizeni)` kde `CisloZakazky LIKE 'Re%ie'`) = už odfakturovaná → orazítkovat `fakturace_obj_id`. Cutoff = 1. den měsíce té objednávky; stampuje se `vw.datum < cutoff`.

Backfill 3.9.2026: 123 řádků u 6 lidí (105:205,26 h; 327:14,82 h; 346:3,45 h; 370:29,56 h; 371:21,98 h; 464:0,51 h), pod existující F0 sentinel `tenant.osvc_vobj.id=1` (migrace_centrala), odlišitelné přes `fakturace_at`. App DOVOLENÁ k razítkování = 0 (dovolená je celá z Centrály, orazítkovaná už F0 seedem). Lidé bez režijní objednávky (nemají cutoff) se NErazítkují — jejich app režie je skutečně nefakturovaná. Ověřeno: Voříšek podklad spadl z ~28 h na 21,57 h = přesně dílenský přehled.

## 3) Budoucí fakturace přes STRATEGII už razítkuje režii sama
`g2007.python` `podklad_osvc_zapis` (tlačítko „Objednávka EC/ES") razítkuje `fakturace_obj_id` na `vyroba_work` i `att_entry` u REŽIE a DOVOLENÉ — podle seznamu ID řádků (`WHERE id = ANY(:ids)`), takže chytá i app řádky. Mezera se tedy nezopakuje, POKUD se fakturuje přes tlačítko STRATEGIE (ne přes Dušanovo generování v Centrále, které `vyroba_work` nerazítkuje).

Souvisí: [[doc-mzdy-podklad-osvc-stare-zakazky-recency-filtr]]

