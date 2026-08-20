# Docházka new — činnost i u právě běžícího úseku

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Docházka new — činnost je vidět i u právě běžícího úseku

> Jirka + Claude‑28, 28. 7. 2026. Schválila Marti‑AI (msg 11412). Změna JEN v zobrazení,
> žádná data se neměnila. Přehled `/dochazka-po-zakazkach`, data_set `dochazka.zakazky_vse_list`.

## Problém (nahlášeno jako „zmizela čísla ve sloupci DruhCinnosti")
Ráno vypadal sloupec `DruhCinnosti` prázdný. Nešlo o chybu ani o ztrátu dat — přehled
prostě zobrazoval převážně **právě běžící úseky**, které číslo činnosti nikdy neměly.

**Proč:** fold `tenant.work_alloc` → `tenant.vyroba_work` bere **jen ukončené úseky**
(`router.py`, `_sync_vyroba_work_app`: `WHERE wa.ended_at IS NOT NULL`). Dokud člověk úsek
neukončí, do `vyroba_work` se nedostane, takže se v přehledu objeví přes větev **P**
(`tenant.att_entry`, přítomnost), kde bylo natvrdo `NULL::smallint` a text `et.label` („Práce").
Ověřeno na datech: 28. 7. v 6:00 byly ukončené jen 3 úseky, 27. 7. jich bylo 97 a všech 97
číslo mělo.

## Řešení
Ve větvi P se u **běžícího** řádku (`e.ended_at IS NULL`) dohledá **otevřený** úsek
z `tenant.work_alloc` (`ended_at IS NULL`, tentýž `user_id`, tentýž den) a vezme se z něj:
- `DruhCinnosti` = `vyroba_cinnost.ec_cislo` (centrálské číslo),
- `CinnostText` = `work_alloc.cinnost_name`, s `COALESCE` fallbackem na `et.label`.

`_cin_id` zůstává `NULL` → **editační formulář ani engine Oprav docházky se nemění**.

## Co je potřeba vědět
- **Činnost v systému nechybí** — je ve `work_alloc` po celou dobu úseku, včetně režie.
  Do přehledu se jen nedostala dřív než po ukončení úseku.
- Kde činnost centrálský protějšek nemá (`ec_cislo IS NULL` — „Bez rozlišení činnosti",
  „ostatní – kanceláře", Režie id 14), zůstane **číslo prázdné a ukáže se jen název**. Správně.
- Kde `work_alloc.cinnost_id` chybí úplně, zůstane původní text „Práce" (fallback).
- **Výkon:** index `ix_work_alloc_user_open (tenant_id, user_id, ended_at)` už existoval,
  nic se nepřidávalo. Naměřeno: výchozí režim 6 531 řádků / 0,9 s; samotné dohledání
  přes celou historii (31 477 řádků větve P) 0,15 s.
- **Záloha:** původní definice je uložená jako `fw.data_set` s kódem
  `dochazka.zakazky_vse_list__zaloha_20260728` (`status='draft'`). Návrat = zkopírovat
  `sql_text` zpátky do `dochazka.zakazky_vse_list`.

## Gotcha pro příště
Když v tomhle přehledu „chybí činnost", **první otázka není „co se rozbilo", ale „je ten
úsek ukončený?"**. Řádek bez konce (`PraceAktivni = ✓`) se bere z docházky, ne z výkazu.

