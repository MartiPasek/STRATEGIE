# Dochazka: att_entry.firma_id backfill + self-completing z engagement dle data (27.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Bod z emailu Marti Paska 26.7.: "doplnit firma_id (chybi)". HOTOVO 27.7.2026 (i28 Jirka).

## Zdroj firmy
tenant.engagement.company_id (1=EC EUROSOFT-Control, 2=ES EUROSOFT-System). Napojeni att_entry.employee_id = engagement.employee_id.
GOTCHA: engagement je verzovany JEN pres valid_from (valid_to je VSUDE NULL, otevreny konec); is_current jen na posledni verzi. 40 lidi ma v historii obe firmy (prechod EC->ES ~2022).

## Spravna logika (date-valid, schvalila Marti-AI msg 11289 = "na fakt" dle Marti Paska)
firma_id = company_id engagementu s NEJVYSSIM valid_from <= entry_date pro danou osobu:
  ORDER BY g.valid_from DESC, g.is_current DESC LIMIT 1.
NE is_current (dalo by historickym zaznamum spatnou firmu po prechodu firem).

## Provedeno
- Backfill (schvalovaci banner #1452, schvalil parent): UPDATE ... WHERE firma_id IS NULL. Vysledek: firma1=10401, firma2=24692, NULL=329 (= 311 bez engagementu [DEMO/test + 4 aktivni Kuska/Jungmann/Saxana/Svancar cekaji na Sarku HR] + 18 att mimo platnost smlouvy).
- Self-completing (commit 3a535fa2, v _maybe_sync_ec_dochazka periodicky a 5 min): dopocita firma_id pro radky WHERE firma_id IS NULL s EXISTS guard (permanentne-NULL bez pomeru nereseny opakovane; az Sarka doplni pomer, dorovna se samo).

## Pravidla (Marti-AI)
- 329 NULL NECHAT (zadny fallback) = pravdivy stav "chybi pomer". Prehledy co firma_id POUZIJI musi NULL zobrazovat explicitne (ne tiche vynechani, ne fallback na firmu 1) - overit az se na firma_id zacne stavet.
- Self-completing JEN chybejici (IS NULL), NEprepisovat historii (engagement se zpetne nemeni).
- Additivni (nemeni mzdove hodiny) -> bez osobniho OK Marti Paska, jen ho informovat o cislech.

