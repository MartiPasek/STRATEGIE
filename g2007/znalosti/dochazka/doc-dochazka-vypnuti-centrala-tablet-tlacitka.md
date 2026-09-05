# Vypnutí docházky v Centrále vynuluje _AuthDochazka → padnou i pracovní tlačítka tabletu (odvozy/beistellung)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## !! POZOR - 5. 9. 2026 se tlacitko v mobilu PREJMENOVALO
> Tlacitko, kterym se v mobilni appce zahajuje prace, se jmenuje **START**.
> Do 5. 9. 2026 se jmenovalo "Makat" - rozhodl Jiri Honomichl. Vecne se nic nezmenilo,
> jen nazev; v textu nize je uz novy. Aktualni stav obrazovky:
> [[doc-dochazka-mobil-dochazka-prejmenovani-a-pravdivost-navodu-5-9-2026]]

> **DOPLNĚNÍ 25. 8. 2026:** Níže uvedené platí pro úroveň **uživatele**. Na úrovni **zařízení** existují samostatné vypínače `TlOdvozy` a `TlBeistellung` v `EC_Dochazka_NastavZar` — viz [[doc-dochazka-odvozy-potvrzovani-stoji-od-22-7-2026]], kde je i doložený výpadek potvrzování odvozů od 22. 7. 2026.

## Kontext
Mechanismus `_ec_vypni_dochazku` (viz [[doc-dochazka-vypnuti-centrala-navrh]]) se spustí při **1. „START"** v mobilní appce STRATEGIE a zapíše do DB_EC pro daného člověka (dle os. čísla → `TabCisZam.ID`):
- `TabCisZam_EXT._AuthDochazka = ''`
- `EC_GlobKonstUziv.PovolitDochVCentrale = 0` (jen má-li Centrála login)

Od 30. 6. 2026 (Jirka) je to **odgateováno na všechny** zaměstnance, jednosměrně, jednorázově (příznak `tenant.att_source_pref.ec_vypnuto_at`).

## GOTCHA (jádro)
`_AuthDochazka` **není jen „píchni příchod/odchod" — je to autorizace CELÉHO docházkového terminálu (tabletu)**. Vynulováním na `''` se člověk z tabletu odhlásí úplně. **Pracovní tlačítka na tomtéž terminálu (typicky „Odvozy", „Beistellung") tím padnou spolu s docházkou.** Není to chyba těch tlačítek — je to vedlejší efekt plošného vymazání terminálové autorizace.

**Symptom:** uživatel po přechodu na „docházku strategie" hlásí, že mu na tabletu zmizela tlačítka odvozy/beistellung.

## Nevratnost + neexistence dílčí hodnoty
- `_ec_vypni_dochazku` je **jednosměrné**; do `fw.ec_dml_log` se loguje **jen NOVÁ hodnota (`''`)**, původní `_AuthDochazka` se nikam neukládá → **bez zálohy Centrály se původní hodnota nedá rekonstruovat**.
- **Neexistuje hodnota `_AuthDochazka`, která by zapnula jen některá tlačítka** (potvrzeno Kristý + Jirka, 30. 7. 2026). Buď má člověk terminál celý, nebo vůbec.

## ROZHODNUTÍ (Kristý + Jirka, 30. 7. 2026)
Terminál v Centrále se **NEobnovuje**. Pracovní akce (odvozy, beistellung) se řeší jako **tlačítka v mobilní appce STRATEGIE** — jdeme cestou appky, ne návratu na tablet. Realizuje Jirka.

## Doporučení do budoucna
- Než se `_AuthDochazka` nuluje, **uložit původní hodnotu** (kvůli vratnosti).
- U lidí, kteří terminál používají i na **práci** (ne jen docházku), nulovat **výběrově**, ne plošně.

## Případ, kde to vyplavalo
Jaroslav Švenda (os. č. 488, `user_id` 67), `att_source_pref.ec_vypnuto_at` = 22. 7. 2026 09:03 (spustil sám prvním „START").

## Zdroje
`modules/erp/api/router.py` — `_ec_vypni_dochazku`, `_ec_set_block_dochazka`, app_checkin · `tenant.att_source_pref` · `fw.ec_dml_log` (via='vypni_dochazka').

