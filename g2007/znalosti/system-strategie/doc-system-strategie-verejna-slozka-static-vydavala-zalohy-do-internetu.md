# Verejna slozka /static vydavala zalohy do internetu - nalez, oprava a pojistka do budoucna (23.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Slozka /static je verejna — cokoli tam zbyde, jde stahnout z internetu

Zapsal Claude-28 (Jirka Honomichl) **23.–24.8.2026**, schvalila Marti-AI (msg 13543).
Vse nize je **zmereno na produkci**, ne odvozeno.

## Nalez

`apps/api/static` je mountovana pres `app.mount("/static", StaticFiles(...))` a **neni za
prihlasenim**. Zbytky po presunu statickych souboru do DB (uklid 5.8.2026) tam zustaly lezet
a **daly se stahnout z internetu** — staci znat jmeno souboru:

| soubor | odpoved | velikost |
|---|---|---|
| `dochazka-opravy.html.DISK-BACKUP-2026-08-05` | **200** | 82 kB |
| `mobile2.html.bak_removed_20260801_194256` | **200** | **932 kB** |
| `_tmp_nodecheck_test.html` | **200** | 47 B |
| + tri dalsi `*.DISK-BACKUP-2026-08-05` | **200** | 7–121 kB |

**Co v nich bylo** (kontrolovano s zamaskovanymi hodnotami, nic se nevypisovalo):
- **ZADNE heslo, klic ani token natvrdo** — vyskyty slov `password` / `secret` jsou nazvy
  poli formulare a promennych v JS
- **285 ruznych adres `/api/v1/...`** = kompletni vnitrni struktura aplikace
- dve pracovni e-mailove adresy kolegyn pouzite jako priklady ve formulari

Neni to unik osobnich dat, ale **je to prozrazeni vnitrni struktury bez prihlaseni** —
a hlavne to byla **zastarala kopie**, o ktere nikdo nevedel.

## ⚠️ Past, na kterou se da naletet: „to servíruje Caddy"

Komentar u mountu tvrdi *„Caddy file_server na cloud APP resi rovnez"*. **Dnes to tak NENI.**
Overeno z hlavicek odpovedi: `Server: uvicorn` + `X-Request-Id` (tedy nase aplikace), a
v `scripts/Caddyfile.*` neni o `static` ani zminka. **Kdyby to servíroval Caddy, oprava
v Pythonu by na produkci nezabrala** — tohle se musi overit DRIV, nez se zacne opravovat.

## Nasazena pojistka (commit `3d3faa67`)

Podtrida `StaticFiles`, ktera **odmitne vydat zalohu nebo docasny soubor**:

- vraci **404, ne 403** — 403 by potvrdilo, ze soubor existuje
- zapise varovani do logu, kdyz o takovy soubor nekdo pozada
- **pri startu projde slozku** a do logu nahlasi, kolik zbytku tam lezi a jak se jmenuji
  (cele v `try/except` — hlidac nesmi nikdy shodit start)

Blokovane vzory: `disk-backup`, `bak_removed`, `.bak`, `.old`, `.orig`, `.save`, `.swp`,
`.swo`, `.tmp`, `.rej`, tilda, a nazvy zacinajici `_tmp`.

**Overeno pred nasazenim i po nem:**
- proti **261 skutecnym souborum** ve `static`: **0 falesnych poplachu** (osahany i zaludne
  pripady `backup-info.html` a `template.js` — projdou spravne)
- po nasazeni vsech sest zbytku vraci **404** (drive 200), sedm beznych souboru dal **200**
- aplikace bezi, `/app/whoami` i `/app/ios/push/register` odpovidaji jako drive

⚠️ **Falesny poplach pri overovani:** `/static/index.html` vraci 404 — ale to je **stary stav**,
ne dusledek pojistky. `index.html` ve slozce vubec neni (presunut do `static_db` pri uklidu 5.8.)
a hlidac ho neblokuje. Overeno oboji, nez se to vyslovilo.

## Co z toho plyne obecne

1. **Do `apps/api/static` nepatri zalohy ani docasne soubory.** Je to verejna slozka, ne odkladiste.
   Pojistka je zachranna sit, **ne nahrada uklidu**.
2. **Kdyz se neco stehuje na nove misto, je potreba odstranit i stary VYSLEDEK** — tohle je
   tataz past jako u dilku mobilu (viz `doc-system-strategie-mobil-fragmenty-v-static-jsou-zastarale-kopie`),
   jen o patro vedle.
3. **Nez opravis servirovani, over, KDO ho dela.** Komentar v kodu nemusi platit.

## Stav souboru samotnych

**NESMAZANY** — Jirka 24.8.2026 rozhodl „pro jistotu nic nemazat". Servirovani je zablokovane,
takze zvenci jsou nedostupne; fyzicky na disku Prahy porad lezi (overeno vypisem: sest souboru,
47 B az 932 kB). Soubor `query` v korenu repa na Praze je take nedotceny — **nikdo nevi, co to je**,
proto se nemazal.

