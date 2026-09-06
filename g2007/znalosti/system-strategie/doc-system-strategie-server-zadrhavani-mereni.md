# Server se zadrhava - mereni 19.8.2026 (VYRESENO 6.9.2026: pamet + obsluha hlaseni ze site na hlavnim vlakne)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Server STRATEGIE se zadrhava - vysledek mereni 19. 8. 2026

Zmereno **50 minut souvisle, 48 766 vzorku**, 15 soubeznych klientu, tri nezavisle HTTP stacky
(curl, Python, prohlizec) + kontrolni cizi server po teze lince. Surova data (7,3 MB TSV) ma
Jirka. Tahle znalost existuje hlavne proto, **aby se nemerily znovu veci, ktere uz vylouceny
jsou**, a aby se neopakovaly drivejsi mylne zavery.

> ## ✅ VYRESENO 6. 9. 2026 — pricina nalezena a opravena
>
> Zadrhavani popsane v teto znalosti melo **dve pricany**, obe uz jsou pryc:
>
> 1. **Malo pameti** na prazskem serveru (4 GB, odkladani na disk) — dodavatel pridal
>    pamet 6. 9. 2026 v 11:47, nove je jich 16 GB. Detail:
>    `doc-system-strategie-praha-server-malo-ram-zatuhavani-api`.
> 2. **Obsluha hlaseni ze site** (`POST /app/netscan/ingest`) byla psana jako `async`
>    a delala 8 vterin praci s databazi primo na hlavnim vlakne — po tu dobu API
>    neobslouzilo nikoho. Bezi kazdych ~5 minut. Opraveno 6. 9. 2026 (`f50d5195`)
>    presunem prace do vlakna. Detail a obecne pravidlo:
>    `doc-system-strategie-async-obsluha-blokuje-cele-api`.
>
> ⚠ Jedna vec nize UZ NEPLATI: mezi vyloucenymi je *periodicita* (Rayleigh, 300 s
> p=0,937). Dnes byla zadrhnuti **presne periodicka po 5 min 9 s**. Duvod rozdilu: 19. 8.
> jeste bezela i pametova pricina, ktera delala tolik nahodneho sumu, ze pravidelnost
> prekryla. Naopak spravne bylo tehdejsi *ZBYVA jedina hypoteza* — synchronni prace
> na event loopu; presne to se dnes potvrdilo.
>
> **Po oprave:** 14 minut mereni, 384 dotazu, zadne zadrhnuti, prumerna odezva 0,045 s
> (pred tim 0,098 s). Mereni a vyloucene priciny nize **plati jako historie** a jsou
> porad uzitecne — nemer je znovu.
>
> *(Doplnil Claude-28 / Jirka Honomichl 6. 9. 2026 vecer.)*

## Co se deje
Server nepravidelne prestane odpovidat. Mezi epizodami je rychly (median 0,10 s), v epizode
ceka **vsechno a vsichni** - mobilni appka (iOS i Android) i web v prohlizeci na pocitaci.

**Nejpoctivejsi metrika je podil CASU, ne pozadavku:** primar nedokazal odpovedet do 1 s po
**39,1 % z 50 minut** (sekundar 2,1 %). Podil pozadavku (9,09 %) problem podhodnocuje, protoze
zamrzly klient jich stihne vyslat min. Epizoda: median 2,65 s, p90 11,2 s, **max 45,7 s**.

Mereno na `GET /api/v1/health` - endpoint, ktery **nesaha do DB, nema autentizaci a jen vrati
konstantu** (`apps/api/main.py:600`, je to `def`). Cokoli, co ho zdrzi, se deje mimo aplikacni
logiku.

## PROKAZANO
- **Zadrhava jen primar:** 9,09 % (1261/13869) vs. sekundar 1,04 % (70/6741), rozdil +8,05 p.b.,
  95% CI [+7,51; +8,59], Fisher **p = 2,8e-140**. Mediany obou shodne.
  ⚠️ **Kauzalne to NEURCUJE pricinu** - primar se lisi dvema vecmi naraz: `lb_policy first`
  na nej posila veskery provoz A bezi na nem ulohy na pozadi.
- **Zamrzne cely proces**, ne jednotlivy pozadavek: jiny klient je pomaly soucasne s p=96,5 %
  (bazal 6,5 %), 70 % z 228 epizod zasahlo vsech 6 klientu. **Keep-alive klient na navazanem
  spojeni zamrza stejne** (11,01 % vs 11,93 %) -> neni to navazovani spojeni ani TLS.
- Zadrhava se **kazda cesta** (`/health`, `/docs`, 404, `/mobile`: 55-69 % behem epizod,
  0,5-1,2 % mimo).
- Na sekundar jde merit napримo pres cookie `strategie_api_version=previous`
  (`Caddyfile.api_version_v2:31`) - obejde `lb_policy first`. Porty 8002/8003 jsou zvenci
  zafirewallovane.

## VYLOUCENO - nemerit znovu
sit/VPN · stroj, antivirus, zaloha, swap (**sekundar bezi na tomtez stroji** a stoji 2,1 % proti
39,1 %) · databaze (mereny endpoint se ji nedotkne) · autentizace · soubeznost a fronta
(12 soubeznych dotazu za 0,19 s) · zatez (pri 1/8 zateze porad 4,36 %) · protokol a knihovna
(reprodukovano tremi stacky) · **periodicita** (Rayleigh na 228 epizodach: 30 s p=0,115,
60 s p=0,396, 300 s p=0,937 - nespousti to naplanovana uloha).

**Drivejsi zavery, ktere premereni VYVRATILO (nesirit dal):** „API se odbavuje seriove" ·
„hrdlem je `pool_size=2, max_overflow=4`" · „neprihlasene rychle, prihlasene pomale" ·
„synchronni SQL v `request_id_middleware`" (pro pozadavek bez cookies se `_sess_restore_from_device`
i `_fi_user_context` preskoci a `_demo_uid_cached()` se nezavola vubec - Python zkratuje `and`
na `main.py:936`) · „drzi to ulohy na pozadi pres GIL".

## ZBYVA jedina hypoteza
Synchronni prace v kodu bezicim na event loopu: **370 ze 726 `async def` endpointu nema jediny
`await`** (302 z nich v `router.py`) a dela v loopu synchronni SQL. Pritezuje `erp_registry.call()`
(`erp_registry.py:36`, SELECT pri kazdem volani i pri cache hitu) a chybejici `pool_size`
v `core/database.py:25` (default 15 spojeni vs. 40 vlaken threadpoolu).

**Zvenci to dal nejde.** Rozhodne **`py-spy dump --pid <uvicorn 8002>` behem epizody** - jedine
mereni, ktere ukaze konkretni zasobnik. Dal: merit cas kolem `await call_next` (`main.py:1006`),
cist `C:/caddy/logs/access.log`, logovat cekani na spojeni z poolu.

## ⚠️ SAMOSTATNY NALEZ - failover se rozkmitava
`health_timeout 2s` + `max_fails 1` + `fail_duration 10s` (`Caddyfile.api_version_v2:81-85`)
znamena, ze **jakekoli zadrhnuti nad 2 s odstavi primar na 10 s**. V datech **66 prepnuti za
5 minut**, behy sekundaru median 0,6 s. Sekundar bezi ze slozky `STRATEGIE-prev`, tedy **starsi
kod** -> uzivatelum se za chodu meni verze aplikace a zpet. Tohle je jedina uprava doporucena
rovnou; samotne zadrhavani nespravi, ale prestane se kvuli nemu menit verze appky pod rukama.

## Vedlejsi (jen pomaly start, nesouvisi)
`GET /mobile` = 1 035 803 B (~993 kB inline JS), servíruje se **nekomprimovane** i pri
`Accept-Encoding: gzip`, s `cache-control: no-store`. Gzip = **3,9x** (na ~267 kB).

