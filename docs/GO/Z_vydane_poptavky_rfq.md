# Vydané poptávky (řada 940) — RFQ sklad dodavatelských nabídek → 4. cenový zdroj enginu

> **Zapsáno: Claude ID23, 18. 7. 2026** (na pokyn Marti „dotáhni si to, pak to podrobně popiš").
> Navazuje na kalkulační engine Vize 1 (viz `Z_kalkulace_ceniky_vize1`) a reálné benchmarky FRIMO/Zalkin.

## 1. Co to je a proč

**Modul „Vydané poptávky" (přehled 240 v Centrále, `TabDokladyZbozi.RadaDokladu='940'`)** je sklad
odeslaných poptávek dodavatelům **a jejich vrácených nabídek** na díly, které EUROSOFT nemá v katalogu
(ceníky/příjemky). Když kalkulant narazí na díl bez ceny (Omron, ILME, Patlite, SEW, HETRONIK, Icotek,
Bernstein…), pošle e-mailem poptávku dodavateli → ten vrátí nabídku (cena, platnost, dodací lhůta) →
dosud se to **ručně přepisuje do kalkulace** (často dvakrát: do modulu i do kalkulace). Tam odtékal čas.

**Cíl:** dotáhnout ta cenová pole do STRATEGIE, aby engine bral **poslední platnou dodavatelskou
nabídku jako 4. cenový zdroj** (vedle příjemky, Velkého ceníku a SiePortalu) — bez ručního přepisování.

## 2. Zdroj v DB_EC (co nese přehled 240)

`TabDokladyZbozi d` (řada 940) + `TabDokladyZbozi_EXT e` (ID=ID). Klíčová EXT pole nabídky dodavatele:

| EXT pole | význam |
|---|---|
| `_Kcen_Cena` | **cena nabídky** dodavatele |
| `_PlatnostDoNabDod` | **platnost do** (dokdy cena platí) |
| `_Sleva` | řádková sleva |
| `_OrgNazevNabDod` | **dodavatel** (kdo nabídku poslal) |
| `_VyrobceNab` | **výrobce** dílu |
| `_PopisNabDod` | popis dílu |
| `_PoznamkaVyvojar` | umístění souboru nabídky (dokument) |
| `_KontaktJmenoNabDod` / `_KontaktNabDod` | kontakt jméno / e-mail |
| `_CisloNabidkyDodavatele` | číslo nabídky u dodavatele |
| `_PoznamkaExt` | číslo nabídky EC import |
| SeznamKalkulací | navázané kalkulace (přes `EC_DokladyVazby.ID_Kam=d.ID` → `EC_KalkulaceHlav.CisloKalkulace`) |

## 3. Co bylo ve STRATEGII PŘED (18. 7.) — jen kostra

`tenant.ec_doklad_zbozi` (generický mirror TabDokladyZbozi, sync `_sync_ec_doklady_zbozi`, řada 940
i `oz_vy_popt`) táhl z `_EXT` jen `_Odeslano/_Oznaceno/_CisloNabidkyDodavatele` — **NE** cenu/platnost/
dodavatele/výrobce. Navíc mirror hlaviček řady 940 byl tenký (34 řádků). → měli jsme kostru, ne ceny.

## 4. Co jsem dotáhl (build 18. 7., commit `eb6945c7`)

- **Nová tabulka `tenant.vypopt_nabidka`** (vlastník **strategie** — `ec_doklad_zbozi` vlastní Marti-AI,
  proto ji strategie nemůže `ALTER`; řešení = vlastní boční tabulka joinovaná přes `src_id`).
  Sloupce: `src_id` (PK = ID dokladu 940), `nab_cena`, `nab_platnost_do`, `nab_sleva`, `nab_dodavatel`,
  `nab_vyrobce`, `nab_popis`, `nab_soubor`, `nab_kontakt_jmeno`, `nab_kontakt_email`,
  `nab_cislo_ec_import`, `seznam_kalkulaci`, `synced_at`. `GRANT SELECT … TO PUBLIC`.
- **Příkazy** (`modules/erp/api/kalkulace_engine.py`, dispatch v `router.py`):
  - `@@VYPOPT SYNC` — načte řadu 940 z DB_EC (EXT pole + STRING_AGG SeznamKalkulací) → upsert do `vypopt_nabidka` dle `src_id`.
  - `@@VYPOPT LIST [filtr]` — přehled (join `ec_doklad_zbozi` + `vypopt_nabidka`): číslo, dodavatel, výrobce, cena, platnost, popis, kalkulace.

**Stav dat po SYNC:** 798 nabídek (od 2024) — **255 s cenou, 716 dodavatel, 712 výrobce, 471 platnost,
490 navázaných na kalkulaci.** Příklady: Siemens 11 733,79 € (do 2026-09-30, EK261671); SEW 817,31 €
(EK263370); HETRONIK 5 308,23 € (EK263370); GHV/Weigel 484,34 € (EK262380).

## 5. Jak se z toho stane 4. CENOVÝ ZDROJ (další krok)

Napojit `vypopt_nabidka` do `@@KALKPRICE`/`compute()`: pro díl (dle výrobce+popis, časem RegCis)
dohledat **poslední PLATNOU** nabídku (`nab_platnost_do >= dnes`) → použít `nab_cena` jako materiálovou
cenu, když chybí příjemka i ceník. Flag zdroje `nabídka(dodavatel, platí do …)`. Prošlé nabídky =
kandidát na novou poptávku. Tím engine odemkne nekatalogové díly a ruší dvojí ruční přepisování.

## 6. Gráble (drž)
- `tenant.ec_doklad_zbozi` **vlastní Marti-AI** → strategie NESMÍ `ALTER` (500). Řešení = vlastní boční tabulka (strategie).
- SQL most (read) **filtruje i slovo `ALTER`** (nejen INSERT/UPDATE/DELETE/DROP) i jako podřetězec — pozor na string literály v diagnostice.
- device_stage_files umí servírovat **STALE** kopii velkého souboru (mount keš dle cesty) — před editem VŽDY ověř `grep -c` vlastních značek; obejít = `cp` na device pod novým jménem → stage nové cesty.
- Mirror hlaviček řady 940 je tenký (34) → LIST joinuje jen ty; plná data (798) jsou v `vypopt_nabidka`. TODO: dotáhnout hlavičky 940 nebo LIST z vypopt_nabidka napřímo.
