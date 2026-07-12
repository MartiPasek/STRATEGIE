# 🔌 Návrh změny: Při zahájení práce v mobilu vypnout docházku v Centrále

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🔌 Návrh změny: Při zahájení práce v mobilu vypnout docházku v Centrále

> **Stav: NÁVRH — čeká na schválení Marti. Bez schválení se NEMĚNÍ.**
> Autor: Claude‑28 (Jirka), 29. 6. 2026. Podnět: Jirka.
> Rozhodnutí pro Martiho jsou na konci (4 otázky, ať nemusíš dlouho zkoumat).

## 1. O co jde (1 odstavec)
Až někdo poprvé **zahájí práci přes mobilní appku** (tlačítko **▶️ Makat**), chceme mu
**trvale vypnout docházku ve staré Centrále** — aby už **nemohl píchat na docházkovém
terminálu** ani pracovat s docházkou v ERP Centrála. Cíl: konec dvojí docházky
(mobil × Centrála). Je to **jednosměrné — zpět to vracet nepotřebujeme** (rozhodnutí Jirka).

## 2. Jak přesně (Jirkova doménová znalost Centrály)
Dvě změny v DB_EC (SQL 192.168.30.11) pro daného člověka dle osobního čísla:
- `TabCisZam_EXT._AuthDochazka = ''` → odebere auth na **docházkovém terminálu**
- `EC_GlobKonstUziv.PovolitDochVCentrale = 0` → zakáže docházku v **ERP Centrála**

**⚠️ Pozor — tohle NENÍ to samé co už máme:** v kódu existuje `_ec_set_block_dochazka`
(`router.py:15527`), které píše `TabCisZam_EXT._BlokovatDochazku=1`. To je ale jen
**reverzibilní BLOKACE**, ne vypnutí. Jirkova dvě pole jsou **trvalé VYPNUTÍ** (terminál +
ERP). Pozn.: `_AuthDochazka`/`PovolitDochVCentrale` zatím v našem kódu nepoužíváme — stojí to
na Jirkově znalosti Centrály, proto níže navrhuju pilota na jednom člověku.

## 3. Návrh implementace (čistě, znovupoužitím existující infrastruktury)
Veškerá „instalatérská práce" už v projektu je — jen ji použijeme:
- **Nová funkce** `_ec_vypni_dochazku(cislo)` vedle `_ec_set_block_dochazka`, stejná cesta:
  EUROSOFT‑MCP (`eurosoft_strategie_update_row`, `db_name="DB_EC"`) + audit do `fw.ec_dml_log`.
  - `SELECT ID, LoginId FROM TabCisZam WHERE Cislo=cislo`
  - `update_row TabCisZam_EXT SET _AuthDochazka='' WHERE ID=<id>`
  - `update_row EC_GlobKonstUziv SET PovolitDochVCentrale=0 WHERE LoginName=<LoginId>`
  - (Kdo nemá Centrála login → GU řádek nedotčen, terminálové pole proběhne tak jako tak.)
- **Spuštění:** v `att_checkin` hned po commitu (`router.py:~19933`, vedle už existujícího
  `_ec_close_open_shift`), **jen při reálném startu** (`not switching and kind in work/overhead`).
- **Jednorázově** (příznak `tenant.att_source_pref.ec_vypnuto_at`) → poprvé vypni + zapiš čas,
  dál přeskoč. (Žádné MSSQL zápisy každou směnu → šetří MCP rate‑limit.)
- **+ `app_only=true`** (reuse `att_source_pref`) → EC import toho člověka přeskočí.
- **Best‑effort** — když EC zápis selže, Makat se NIKDY nezablokuje (jako u `_ec_close_open_shift`).
- **Žádná reverzní funkce** (jednosměrné, dle rozhodnutí). Audit `fw.ec_dml_log` jen jako stopa.

**Osobní číslo se nemusí nikde hledat** — je to `tenant.att_employee.cislo_zam` (numerické =
`TabCisZam.Cislo`), které appka už dnes používá k zápisu do Centrály.

## 4. Dopady / bezpečnost
- Zápis do **produkční legacy ERP (Centrála)** s **mzdovými/terminálovými dopady** → proto pilot.
- **Trvalé + automaticky = i omyl/test je natrvalo.** Kdo appku jen vyzkouší a klikne Makat,
  trvale se odřízne od Centrály bez návratu (viz otázka 2).
- Komplementární s tím, co už běží: `_ec_close_open_shift` (zavře otevřenou EC směnu při Makat),
  `_mirror_att_to_ec` (mobilní docházku zrcadlí do Centrály pro mzdy), `app_only` (EC import skip).

## 5. 🟢 ROZHODNUTÍ PRO MARTIHO (stačí odpovědět 1–4)
1. **Pole:** Potvrzuješ `_AuthDochazka=''` + `PovolitDochVCentrale=0` jako správný „vypínací"
   mechanismus? (V kódu zatím nepoužité; `_BlokovatDochazku` je jen blok, ne vypnutí.)
2. **Trigger:** Automaticky při **1. Makat** (Jirkův záměr) — OK? Nebo radši **vědomý HR přepínač**
   (bezpečnější, protože vypnutí je trvalé a auto = i omyl/test natrvalo)?
3. **Dvě cesty:** Necháváme obě — tvůj reverzibilní `_BlokovatDochazku` (HR blok) i nové trvalé
   vypnutí (Makat)? Nebo sjednotit na jednu?
4. **Pilot:** OK spustit to **nejdřív jen na Jirkovi (os. č. 9030)** a ověřit v Centrále, než to
   zapneme všem?

Po tvém schválení (a odpovědích) to Claude‑28 postaví přesně dle tohoto návrhu. Do té doby **nic neměníme.**


