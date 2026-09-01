# HR spis: migrace z Centrály bere celý strom a deduplikuje podle složky (oprava 1. 9. 2026)

> oblast: `osoba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co migrace dělá

`POST /app/hr/spis-migrate` (karta zaměstnance → Dokumenty → „⬇ Načíst z Centrály") přenáší osobní spis ze souborové složky Centrály `KZ<cislo_zam>` do `tenant.employee_document`. HR-gated (`_hr_can_manage`), auditované (`_doc_log`), idempotentní, `commit=false` = jen náhled plánu.

Od 1. 9. 2026 kód žije v **`g2007.python` `hr_spis_migrate`**, v `router.py` je jen tenký delegate. Seznam dokumentů pro kartu je taktéž v DB — **`g2007.python` `hr_person_docs`**.

## Dvě opravy z 1. 9. 2026 (zadala Kristý, C24)

**(1) Rekurze do hloubky.** Původní kód procházel kořen a **jen jednu úroveň** podsložek; hlubší adresáře **tiše přeskočil** — v plánu se neobjevily a nikde nebyla zmínka, že něco chybí. U č. 498 (Artim) takhle vypadly `Ostatní/Daně/2024/Artim.pdf` a `Ostatní/Daně/2025/Artim.pdf` (plán ukazoval 27 z 29 souborů). Nyní BFS přes celý strom, `MAX_HLOUBKA=8`, `MAX_SLOZEK=400`. Složka, kterou se nepodaří přečíst, se hlásí v `chyby_slozek` — nezmizí.

**(2) Deduplikace podle složky, ne jen názvu.** Původně stačila shoda `nazev` → tentýž název ve dvou složkách se přeskočil. Adresáře navíc chodí v listingu **před** soubory, takže se nejdřív naimportovala **archivní** kopie se stavem `archiv` a **platná verze z kořene se zahodila**. U č. 498 se to týkalo pracovní smlouvy — nejdůležitějšího dokumentu ve spisu.

Nyní: **kořen se zpracuje první** a klíč je `(zdroj_slozka, nazev)`. Zdrojová složka se ukládá do nového sloupce **`tenant.employee_document.zdroj_slozka`** (`varchar(400)`, `''` = kořen; ALTER req #2650). Řádky z dřívějších importů mají `zdroj_slozka` NULL — ty se poznávají jen podle názvu, aby se nezdvojily. Karta složku zobrazuje šedě u názvu (`📁 Ostatní/Daně/2024`) a náhled migrace ukazuje celou cestu.

## Co zůstalo beze změny

Stav: podsložka s `archiv` **kdekoli v cestě** → `archiv` (K archivaci), vše ostatní → `platny` (Platné). Zařazení do kategorie podle názvu (`_mig_kategorie`). HR gate, audit, idempotence.

## Předpoklad, bez kterého migrace nevidí nic

`tenant.dir_config_storage` id 26 (`osoba_hr`) a 27 (`osoba_me`) musí mít **server-lokální** `root_path = D:\Data\Zamestnanci`, ne UNC — viz [[doc-provoz-eurosoft-mcp-root-path-lokalni-ne-unc]]. Do 31. 8. 2026 tam byl UNC tvar a sekce „Dokumenty z Centrály" svítila `(0)`.

## Otevřené — rozhodnout před hromadnou migrací všech 77 lidí

Podsložka `Ostatní` obsahuje u některých lidí **skeny občanských průkazů** (`OP_1`, `OP_2`), daňová přiznání a `CandidateReport`. Než se pustí bulk (`/app/hr/spis-migrate-all`), je potřeba potvrdit se Šárkou, které typy dokumentů do digitálního šanonu vůbec patří — kopii OP je z hlediska GDPR jednodušší nenamigrovat než ji potom mazat. **Neřešeno, čeká na rozhodnutí.**

