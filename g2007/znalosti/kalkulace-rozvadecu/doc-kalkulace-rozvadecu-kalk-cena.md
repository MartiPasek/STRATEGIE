# proj.kalk_cena — cenová vrstva dílů (nový model) + nesoulad enginu tenant/proj

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# proj.kalk_cena — cenová vrstva dílů (nový model)

**Autor: Claude-24 (Kristý), 24. 7. 2026** (req #1399, po svolení Martiho k rebuildu). Ceny dílů z různých zdrojů, návazné na katalog `kalk_kmen` a číselník `cena_zdroj`.

## Struktura (dle zadání Kristý)
`proj.kalk_cena`: `id` (bigint identity, PK), `tenant_id` (default 2), `id_kalk_kmen` (→ FK `proj.kalk_kmen(id)`), `zdroj` (text), `cc` (numeric), `rabatt` (numeric), `nc` (numeric), `zdroj_typ` (→ FK `proj.cena_zdroj(id)`), `id_zdroj_hlav` (bigint, např. ID ceníku/nabídky), `id_zdroj_pol` (bigint, např. ID položky ceníku/nabídky), `created_at`. Indexy na `id_kalk_kmen` a `zdroj_typ`. Zatím prázdná, plní se z jednotlivých zdrojů. Viz číselník [[cena-zdroj-ciselnik]], katalog [[kalk-kmen-standard-load]].

## Co nahradila
Stará `proj.kalk_cena` (2 508 řádků: 2029 `ec2014` baseline + 479 `std2026`) byla stará generace (PK `ec_id`, jen `cc_cena`, zdroj jako text) — engine baseline. Marti schválil rebuild na nový model, stará DROPnuta.

## ⚠️ GOTCHA — nesoulad schématu v kalkulačním enginu (patří C23/Marti)
`modules/erp/api/kalkulace_engine.py` čte/zapisuje **`tenant.kalk_*`** (kalk_cena/kalk_kmen/kalk_koef/kalk_rabat/kalk_skupina…), ALE tyto tabulky reálně existují jen v **`proj`** (v `tenant` žádné `kalk_*` nejsou). `_t` v enginu = `sqlalchemy.text` (ne přepis schématu). Čili engine, jak je napsaný, na reálné tabulky nemíří — buď WIP, nebo chce opravit `tenant.` → `proj.`. **Před napojením kalk_cena na výpočet to musí prověřit C23/Marti** (vlastníci enginu). `_SRC_PRIO` v enginu = STANDARD (`std%`) přebíjí `ec2014`.

## Co je pro kalkulace v tenant.* (inventura 24.7.)
Jen zrcadla z Centrály (read-only): `ec_kalkulace` (1032), `ec_kalkulace_hlav` (1647), `ec_kalkulace_pol` (26142), `ec_kalkulace_polozka` (43274). Plus dvě prázdné nativní: `kalkulace`, `oz_kalkulace`. Všechny nativní `kalk_*` (kmen/cena/koef/rabat/skupina/sestava) jsou v `proj`.

