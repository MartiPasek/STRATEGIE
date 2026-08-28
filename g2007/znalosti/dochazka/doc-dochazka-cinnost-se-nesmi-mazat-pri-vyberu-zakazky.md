# Činnost se nesmí mazat při výběru zakázky — Zemanova díra (Peťa 27. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Činnost se nesmí mazat při výběru zakázky

**27. 8. 2026, Peťa + C26.** Pavlu Zemanovi devět pracovních dní vznikaly úseky rozpadu
bez činnosti (~40 h) a nikdo si toho nevšiml.

## Pravidlo (Peťa + Týnka)
**Bere se zakázka a ta činnost, jaká je zadaná, dokud si ji člověk sám nezmění.**
Systém ji nikdy nesmí přepsat na prázdno.

## Co bylo špatně
Při výběru zakázky (`/app/work/set-zakazka`, `set-rezie` v `router.py`) se činnost
dohledávala v paměti `tenant.work_last_cinnost` pod klíčem = číslo zakázky. Dvě chyby
v jednom místě:

1. **Filtr na druh činnosti.** Čtení mělo `c.kind='standard'`, jenže k zakázce **Rezie**
   si lidé vybírají činnosti druhu `rezie` („Bez rozlišení činnosti", „Ostatní – výroba",
   „Nakládka zakázky"). Pod `ctx='Rezie'` bylo **13 uložených činností a všechny druhu
   `rezie`, se `standard` ani jedna** — paměť se tedy netrefila NIKDY, ne někdy.
2. **Když nenašlo, uložilo prázdno.** `_wp_save(..., cinnost_id=None)` přepsalo
   `tenant.work_pref` na prázdno. Od té chvíle každý nový úsek (`att_wa_open` kopíruje
   předvýběr) vznikal bez činnosti.

Past se sama nerozmotá: opakovaný výběr téže zakázky vede na tentýž filtr a zase uloží
prázdno. Jediná cesta ven byla ručně ťuknout na činnost.

**Zeman:** 10.–18. 8. dvanáct úseků, všechny s činností. 18. 8. v 16:26 si vybral
zakázku Rezie → předvýběr vynulován. 19.–27. 8. **patnáct úseků z patnácti prázdných.**

## Oprava (nasazena 27. 8. 2026, commit e4514afa)
`modules/erp/api/router.py`, obě cesty (`set-zakazka` i `set-rezie`):
- filtr změněn na `c.kind IN ('standard','rezie')` — nepřítomnosti do práce nepatří,
- když paměť nic nenese, **zůstane, co v předvýběru je** (`_wp_get` fallback), nemaže se.

Ověřeno na živých datech: ze 32 lidí se zakázkou Rezie v předvýběru by se do 27. 8.
činnost smazala **všem**; po opravě žádnému. Zemanovi se navíc jeho vlastní zapamatovaná
činnost („Bez rozlišení činnosti") vrátila do předvýběru.

## Hlídače, aby se to neopakovalo
- **Nález ve frontě Oprav `chybi_cinnost`** (`att_anomaly_scan`, R9) — dvojče k Kristýnině
  `chybi_zakazka` (R7). Okno 14 dní, práh 0,1 h, výjimka na lidi, kteří se nekontrolují.
  Úklid: nález sám zmizí, jakmile se činnost doplní. Záloha: `att_anomaly_scan__zaloha_20260827`.
- **Pojistka `rozpad-usek-bez-cinnosti`** — žádný ukončený úsek nad 0,1 h za posledních
  7 dní nesmí být bez činnosti.

## Gotcha
**Na `router.py` nejde napsat pojistku** — hlídací pravidla čtou jen databázi. Tyhle dva
endpointy podle pravidla Marti (2. 8. 2026) na disku ani nemají žít. Až se budou migrovat
do `g2007.python`, půjde ohlídat i tohle.

## Srpnová data
68 úseků bez činnosti (163 h). Doplněno 27. 8.: 43 kancelářských → „Bez rozlišení činnosti"
(pokyn Peti), 18 minutových ve výrobě → činnost převzatá z okolního úseku, Šárce 2 úseky
zakázka Rezie. Zbylých 8 (výroba) doplnil Dušan Havlát ručně v Opravách týž den.

Souvisí: [[doc-dochazka-zakazka-a-cinnost-nemaji-vazbu]] · [[doc-dochazka-dva-ciselniky-druh-zaznamu-vs-cinnost]]

