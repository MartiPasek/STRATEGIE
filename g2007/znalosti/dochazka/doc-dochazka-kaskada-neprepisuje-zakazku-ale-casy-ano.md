# ZRUŠENO — tento zápis tvrdil nesprávně, že kaskáda vrací časy z Docházky new

> ⛔ **TATO ZNALOST UŽ NEPLATÍ — stav `zruseno`.** Neřiď se jí a necituj ji. Zůstává tu jen kvůli historii; zdroj pravdy je databáze `g2007.znalost`.

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `zruseno` · rozsah: globální (všichni tenanti)


# ZRUŠENO 7. 9. 2026 — tento zápis byl nesprávný

Tvrdil, že úprava času v „Docházce new" se tiše vrátí, protože se nenasadí `local_lock`.
**Neplatí.** Editace v Docházce new jde od 3. 8. 2026 přes opravárenský engine
(`fix/polozka` / `fix/entry`), který hlavičku přepočítá a `local_lock` nasadí,
takže kaskáda úpravy nepřepisuje.

Chyba vznikla čtením endpointu `/app/dochazka-zak-tab/save` bez ověření, kdo ho volá.
Ten endpoint dnes ukládá jen poznámku, a schválně se starými časy.

**Platný zápis:** [[doc-dochazka-editace-v-dochazce-new-jde-pres-opravarsky-engine]]

Jediná část původního zápisu, která platí dál: kaskáda `att_sync_vyroba_work`
ve svém UPDATE mění `att_entry_id`, `od`, `konec` a `hodiny` — **`zakazka_ref`
ani `cinnost_id` nesahá nikdy**. To je v platném zápisu taky.

