# Tři vady v mobilu (26. 8. 2026)

Ahoj Jirko,

když jsme opravili, aby se nemoc, OČR a lékař z mobilu nezapisovaly do docházky, zkoušela
jsem to naostro přes „Tady budu jinde". **Data jsou v pořádku** — nic se nezapsalo,
notifikace vedoucímu chodí. Špatně je to, co vidí člověk:

1. **OČR** — po Potvrdit hláška „nepovedlo se uložit", i když se všechno povedlo.
2. **Nemoc** — obrazovka nereaguje vůbec a přijdou **dvě** notifikace, každá jiná
   (a jedna z nich má termíny z OČR). Vypadá to, že mobil volá dvě místa naráz.
3. **Lékař** — taky „nepovedlo se uložit", notifikace dorazila se zpožděním.

Server vrací `ok: true, created: 0` — nula je správně, nic se zapisovat nemá. Tipujeme,
že si mobil ověřuje `created > 0` a nulu bere jako chybu, ale **neověřovali jsme to**.
Do kódu appky jsme nesahali.

**Claude‑26 / Peťa**
