# Rozdělení dne kvůli pauze nechalo druhou část bez rozpadu — kaskáda se ptala před ořezem (Peťa 9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 9. 9. 2026.** Navazuje na `doc-dochazka-pauza-doprostred-prace-rozdeli-zaznam` (8. 9. 2026) — tohle je díra, kterou to rozdělení nechalo.

## Co se stalo

Pavel Zeman, 3. 9. 2026 (rozdělovala Peťa 8. 9. při ostrém testu). Práce 07.33–16.56, 9,38 h se rozpadla na práci 07.33–12.00 (4,45 h), pauzu 12.00–13.00 a práci 13.00–16.56 (3,93 h).

Rozpad na zakázky (`tenant.vyroba_work`) ale zůstal JEDEN — 4,45 h na první část. K úseku 13.00–16.56 nevznikl žádný. Odtud dva nálezy: „chybí rozpad k úseku 13.00–16.56" a „docházka 8,38 h proti rozpadu 4,45 h".

## Příčina

`att_sync_vyroba_work` (kanonická kaskáda) si nejdřív sestaví CELÝ plán a teprve pak zapisuje — `dry_run` se vrací před zápisovou částí. Při sestavování plánu se u každého úseku ptá, jestli už rozpad existuje, a bere i **časový překryv**, ne jen shodné `att_entry_id`.

V tu chvíli původní řádek rozpadu ještě sahal 07.33–16.56, takže se překrýval i s druhou částí → `skip_exists` → nezaloží se nic. Ořez toho řádku na 12.00 přišel až v zápisové fázi. Kontrola se tedy ptala na stav PŘED vlastním ořezem.

## Stav k 9. 9. 2026

- Data srovnána — chybějící úsek 13.00–16.56 (3,93 h, zakázka Rezie, činnost 43 podle předchozího úseku) doplněn ručně ve stejném tvaru, jaký zakládá kaskáda (`source_system='sync'`, vazba na `att_entry_id`). Součet 4,45 + 3,93 = 8,38 h sedí na docházku.
- **Rozdělení dne se do 9. 9. použilo jen jednou** (Zeman 3. 9.), takže jiné dny tímhle nepřišly o rozpad. Ověřeno hledáním poznámky „rozdeleno na" v `att_entry`.

## Oprava kaskády (nasazeno 9. 9. 2026)

`att_sync_vyroba_work`, větev `if settled and create_missing`. Před smyčkou přes úseky se sestaví množina `_menene` = řádky, se kterými tenhle běh sám hýbe (`plan["clip"]`, `plan["deactivate"]`, `plan["dedup_off"]`), a dotaz „už tu rozpad je?" je vynechává (`AND id NOT IN (...)`). Po zápisu plánu totiž nepokrytý úsek krýt nebudou.

Duplicitu to způsobit nemůže — ořezaný řádek vždy padne dovnitř SVÉHO úseku a úseky docházky se navzájem nepřekrývají. Do `plan` přibylo pole `vynechano_z_kontroly` pro dohledání.

Syntaxe ověřena `compile()` nad zdrojem staženým z databáze.

## Platí pro mobil i Opravy

Rozdělení pauzou nabízí i mobilní aplikace (`mobile.html`, `fix/add` s `deleni_umim=true`) a volá tutéž kaskádu, takže oprava platí na obou místech. Kaskádu celkem volá 14 funkcí — opravy (`fix/entry`, `fix/add`, `fix/void`, `fix/merge`, `fix/move_day`, `fix/polozka`, `fix/resync`), mobil (`att_checkout`, `att_do_att_action`, `att_wa_open`, `att_confirm_day`) a automaty (`att_auto_checkout_midnight`, `att_anomaly_scan`). Změna je pro všechny stejná a jen zpřesňuje kontrolu, nemění pořadí zápisu.

