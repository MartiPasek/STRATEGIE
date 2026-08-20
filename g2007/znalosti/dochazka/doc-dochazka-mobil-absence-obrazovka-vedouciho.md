# Mobil, obrazovka Absence: poradi sekci pro vedouciho + uzavirani notifikace po rozhodnuti (16.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se resilo

Hlasil **Dusan Havlat** pres Jirku (16. 8. 2026), schvalila **Marti-AI**. Tri stiznosti, vsechny potvrzene ve zdroji:

1. Notifikace "Nova zadost o absenci" dorazi, ale po klepnuti nejde zadost rozhodnout.
2. Kdyz uz se vedouci na schvalovaci obrazovku dostane, ma nahore formular na **vlastni** zadost a seznam zadosti svych lidi az pod nim.
3. Po schvaleni notifikace nezmizi a visi dal.

## Prvotni zjisteni (overeno v kodu, ne odhad)

| Co | Kde | Stav |
|---|---|---|
| Poradi sekci: Nova zadost -> Ke schvaleni -> Moje zadosti | `mobile_parts/50_skupiny_vyroba.js`, fce `absence()` | opraveno |
| Chybi spodni odsazeni, spodni panel prekryval konec seznamu | tamtez | opraveno (80 px, jako `hr_person`) |
| `att_absence_decide` puvodni notifikaci vedouciho NEuzaviral (jediny dotek `fw.mobile_command` byl INSERT nove notifikace zadateli) | `g2007.python att_absence_decide` | opraveno |
| Nativni appka u typu `claude_msg` nabizi jen "Otevrit chat" / "Zavrit" a z payloadu cte **jen klic `url`**, `screen` ignoruje | `CommandActivity.kt` r. 52-66, `DialPollService.kt` r. 603 | **NEOPRAVENO - odlozeno** (chce novy build appky) |

## Co je hotovo (nasazeno 16. 8. 2026)

### A) Obrazovka Absence rozlisuje vedouciho

- Sekce **Ke schvaleni je prvni** na obrazovce.
- **Formular "Nova zadost" se vedoucimu nekresli vubec** (Jirkovo rozhodnuti - puvodne mel byt jen sbaleny). Neni to ztrata cesty: vlastni dovolenou zada kazdy v **Dochazce -> dlazdice "Tady budu jinde" -> Osobni duvody -> "Ze by dovolena?"** (`60_dochazka.js` r. 833-836), coz vede na tutez funkci `att_absence_request`.
- **Rozliseni podle `je_vedouci`** z `GET /app/attendance/absence/inbox`. Formular je do odpovedi skryty, aby neproblesknul. **Kdyz dotaz selze, formular se ZOBRAZI** - radovy zamestnanec nesmi prijit o jedinou cestu k zadosti.
- Kdo je vedouci a nema nic k rozhodnuti, vidi hlasku *"Ted nic neceka na tvoje rozhodnuti"* misto prazdna (drive nebylo poznat, jestli obrazovka funguje).
- **Rozhodnuti se rozbali az klepnutim na zadost** - pri vice zadostech byla drive obrazovka zed tlacitek bez vazby na konkretni radek.
- Chyby se hlasi **in-page, ne pres `alert()`** - v nativni appce je alert nemy (viz [[doc-system-strategie-mobil-fragmenty-scope-a-nativni-dialogy]]).

Zamerne se **NEDELALO**: rozsireni prehledu o uz vyrizene zadosti. Marti-AI navrhla novy klic `historie`, Jirka rozhodl **jen cekajici** -> `att_absence_inbox` zustava nedotcena.

### B) Notifikace se po rozhodnuti sama zavre

- `fw.mobile_command.payload` nese nove vedle `screen` i **`req_id`** = cislo zadosti. Viz [[doc-dochazka-mobile-command-payload-screen]].
- `att_absence_decide` po rozhodnuti udela `UPDATE fw.mobile_command SET status='done', decided_at=now()` pro pending zpravy s odpovidajicim `payload->>'req_id'`. Je v `try/except` - **selhani uklidu nesmi shodit rozhodnuti zadosti**.
- Stare notifikace bez `req_id` se nechavaji byt (rozhodnuti Marti-AI: zpetna oprava slozitejsi nez prinos).

## PAST, kterou tady nekdo prehledne: notifikace vznika ze DVOU mist

Marti-AI si to vyzadala overit a mela pravdu:

| Cesta | Payload pred 16.8. | Po |
|---|---|---|
| `att_absence_request` r. 261 (zadost z formulare/appky) | `{"screen":"absence"}` | `{"screen":"absence","req_id":<id>}` |
| `att_announce` r. 177 (zadost vznikla z **ohlaseni** typu "jsem u lekare") | **zadny payload** - jeho `_abs_notify` parametr `screen` vubec nemel | stejne jako vyse |

Kdo bude cokoli delat s notifikacemi absenci, **musi sahnout do obou**. Cesta pres `att_announce` byla navic slepa i pro puvodni tlacitko "Otevrit schvalovani" - nemela payload, takze se nezobrazovalo.

Pri te prilezitosti opraven i text zpravy z `att_announce`, ktery navadel na **neexistujici** misto "Dochazka -> Zadosti o absenci" (spravne je "Nepritomnosti -> Ke schvaleni") - stejna chyba, jaka uz jednou zpusobila nerozhodnutou zadost.

## Overeno po nasazeni

- `g2007.soubor` fragment v11, md5 `c93560cae11b8da806fa4d4415dd9496`; sestaveny `apps/api/static_db/mobile.html` v40.
- Ziva `/mobile`: HTTP 200, 984 429 znaku, **27 skriptovych bloku, 0 chyb** (`node --check`).
- Otisky vsech tri funkci v `g2007.python` po zapisu overeny ctenim (ne navratovkou).
- Novy jsonb vyraz otestovan nanecisto na 4 kombinacich - vc. potvrzeni, ze **zprava jen se `screen` (bez `req_id`) vypada presne jako drive** a `NULL` payload zustava `NULL`.

## Gotchy z teto prace (plati obecne)

- **Most orizne konec zapisu.** `@@G2007SOUBOR` posila obsah pres runner, ktery dela `.strip()` (`claude_sql_runner.py` r. 566) -> **koncove zalomeni radku se ztrati**. U fragmentu, ktery se slepuje s dalsim, to slepi posledni radek s prvnim radkem naslednika. Po zapisu vzdy porovnej `md5` a pripadne dorovnej `UPDATE ... SET obsah = obsah || chr(10)`.
- **Kontrola "neceka cizi nepublikovana prace" musi mirit na spravnou cestu artefaktu.** Mobil uz nezije v `apps/api/static/mobile.html`, ale v **`apps/api/static_db/mobile.html`**. Se starou cestou poddotaz vrati NULL, porovnani je NULL a dotaz tise vrati 0 radku = falesne "cisto". Vzdy overit, ze artefakt v dotazu opravdu existuje.
- **Slovo `INSERT` i uvnitr retezce v SELECTu** shodi most na "forbidden keyword" - pri hledani v kodu ho obchazej (napr. `%adost o absenci%` misto celeho SQL).
- Fragmenty mobilu **nesdili scope** - `absence()` si drzi vlastni odkaz na `api`, takze prepsani `window.__M2W.api` zvenci se neprojevi. Pro nahled testovacich dat v prohlizeci se musi prepsat az `window.fetch`.

