# EUROSOFT MCP: root_path musí být server-lokální (D:\Data\...), ne UNC — a LISTREC chyby tiše polyká

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Pravidlo

**`tenant.dir_config_storage.root_path` u `backend='eurosoft_unc'` musí být cesta LOKÁLNÍ NA EC-SERVER2** (`D:\Data\...`), **nikdy UNC** (`\\192.168.30.11\...`), přestože se backend jmenuje „unc".

Důvod: EUROSOFT MCP server **běží přímo na 192.168.30.11** (EC-SERVER2, Plzeň — viz [[doc-provoz-topologie-serveru-praha-plzen]]). Když dostane UNC cestu na vlastní share, jde o **loopback sám na sebe** a servisní účet dostane `PermissionError: [WinError 5] Přístup byl odepřen`. Není to chybějící právo ani odpojený konektor — týž adresář přes lokální cestu přečte okamžitě.

UNC podobu si appka **dodělá sama až pro zobrazení** — `_display_path()` v `modules/erp/api/directories.py` má mapu `_SERVER_TO_UNC = [("D:\\Data", "\\\\192.168.30.11\\data")]` a používá ji pro tlačítko „Otevřít složku" v Průzkumníku klienta. Do DB tedy patří lokální tvar, do UI se UNC objeví samo.

## Důkaz (31. 8. 2026, C24/Kristý, přes most)

| příkaz | výsledek |
|---|---|
| `@@FILES LIST \\192.168.30.11\Data\Zamestnanci\KZ498` | `PermissionError: [WinError 5]` |
| `@@FILES LIST D:\Data\Zamestnanci\KZ498` | OK — `Archiv`, `Ostatní` + 4 soubory |
| `@@FILES LISTREC D:\Data\Zamestnanci\KZ498` | OK — 29 souborů rekurzivně |

## ⚠️ Gotcha: `@@FILES LISTREC` chyby z MCP TIŠE POLYKÁ

`LISTREC` (`router.py`, větev `op == "LISTREC"`) na rozdíl od `LIST` **nekontroluje `r.get("ok") is False`**. Když MCP vrátí chybový dict, `items` vyjde prázdné a příkaz hlásí **`0 řádků`** — vypadá to jako prázdná složka, i když jde o `WinError 5`.

**Diagnostikuj vždy přes `@@FILES LIST`**, který chybu ukáže. `LISTREC` používej až potom, na potvrzené cestě. Tahle past stála tým několik dní: `0 řádků` z `LISTREC` bylo v předávce interpretováno jako „konektor je připojený, ale složka je prázdná" → hledal se restart konektoru a práva na serveru, místo jednoho řádku v DB.

## Historie nálezu

Migrace HR osobních spisů z Centrály (`osoba_hr` → `tenant.employee_document`) nešla zprovoznit — v kartě zaměstnance svítilo `(0)`, přestože Šárka soubory přes namapované `Z:` viděla. Předávka od C25 navrhovala reconnect MCP a doplnění práv správcem serveru (Martin). Skutečná příčina byl `root_path` v UNC tvaru u `tenant.dir_config_storage` **id 26 (`osoba_hr`) a 27 (`osoba_me`)**. Opraveno na `D:\Data\Zamestnanci` (write request #2644, schválila Kristý 31. 8. 2026) — složka se načetla okamžitě, bez zásahu na serveru.

Vzor správné konfigurace měl už předtím řádek **id 25 (`poptavky`) = `D:\Data\poptavky`**. Ostatní řádky `dir_config_storage` (id 4–22) mají UNC tvar — **při jejich příštím použití počítej s tímtéž problémem a přepiš je na `D:\Data\...`**.

Souvisí: [[doc-go-strategie_lookupy_adresar]] (dir_config + resolver + protokol eurosoftdir://), [[doc-go-adresar_ec_orgadresare]] (zdroj pravdy v Centrále).

