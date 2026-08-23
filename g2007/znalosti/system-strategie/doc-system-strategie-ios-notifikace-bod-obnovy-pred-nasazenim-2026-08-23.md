# iOS notifikace (APNs): bod obnovy poriseny tesne pred nasazenim PR 5 (23.8.2026) + co se od te doby zmenilo

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Bod obnovy pred nasazenim iOS notifikaci (23.8.2026 18:30 UTC)

Poridil Claude-28 na zadani Jirky Honomichla ("napred chci bod obnovy prave v tomto
okamziku"), schvalila Marti-AI (msg 13414). Vsechny hodnoty nize jsou CTENE v tu chvili -
stav evidence kodu z GitHubu, stav databaze pres SQL most. Nic neni prevzate ze starsich
poznamek. Ucel: umet se vratit sem zpatky, kdyby se nasazeni nepovedlo.

> ⚠️ **CTI NEJDRIV POSLEDNI KAPITOLU "CO SE OD TE DOBY ZMENILO".** Ctyri udaje nize uz
> NEPLATI. Text zustava jako zaznam stavu k 18:30 UTC, ne jako navod pro dnesek.

Souvisejici: `doc-system-strategie-mobil-ios-notifikace-apns` (jak jsou notifikace udelane),
`doc-system-strategie-ios-build-upload-a-past-dvou-contentview`.

## Co se menilo (a tedy co se timhle vraci)

| # | Misto | Co se stalo | Navrat |
|---|---|---|---|
| 1 | evidence kodu (git) | slouceni PR 5 | bod A |
| 2 | `fw.ios_push_token` | zahozeni, aplikace si ji zaklada znovu | bod B |
| 3 | `fw.ios_push_sent` | vznikne (predtim neexistovala) | bod C |
| 4 | `fw.app_secret` | pribudou dva klice od Applu | bod D |
| 5 | knihovny na serveru | `h2` + `pyjwt[crypto]` | bod E |
| 6 | bezici aplikace | nasazeni nove verze | bod F |

## A) Evidence kodu

- **main v tu chvili = `d3ef0cf1a5abdd2374a3d932c6685e5283a23b70`** (23.8.2026 17:11 UTC,
  "fix(hr): zmena pomeru uz uvazek neprepisuje v platnem radku...")
- Jirkuv Windows notebook byl na teze zmene (srovnano na zacatku session).
- Slucovalo se: PR `MartiPasek/STRATEGIE#5`, spicka `f97b00dd`, +1528 / -26, 14 souboru,
  vetev `GHubGeorge:feat/ios-push-server` -> `MartiPasek:main`. Stav OPEN, slucitelnost cista.

**Navrat:** slouceni se NEMAZE, ale ODVOLA - `git revert -m 1 <cislo slouceni>` a nasadit.
Vzdy pres most, nikdy rucne z prikazove radky (gotcha .git/index.lock).

## B) `fw.ios_push_token` - presny predpis, jak vypadala

**0 radku** (zahozenim se neztratila zadna data). Vlastnik role `Marti-AI`;
sekvence `ios_push_token_id_seq` rovnez vlastnik `Marti-AI`.

Sloupce (13, v poradi):

1. `id bigint NOT NULL DEFAULT nextval('ios_push_token_id_seq'::regclass)`
2. `user_id integer NOT NULL`
3. `device_token text NOT NULL`
4. `app_key text NOT NULL DEFAULT 'mobile'::text`
5. `platform text NOT NULL DEFAULT 'ios'::text`
6. `app_version text`
7. `device_id text`
8. `apns_env text`
9. `active boolean NOT NULL DEFAULT true`
10. `last_error text`
11. `last_sent_at timestamp with time zone`
12. `created_at timestamp with time zone NOT NULL DEFAULT now()`
13. `updated_at timestamp with time zone NOT NULL DEFAULT now()`

Omezeni: `ios_push_token_pkey` PRIMARY KEY (id) · `ios_push_token_device_token_key`
UNIQUE (device_token).

Indexy: `ios_push_token_pkey` (unik. nad id) · `ios_push_token_device_token_key`
(unik. nad device_token) · `ix_ios_push_token_user` nad `user_id` jen kde `active`.

Prava: `Marti-AI` = SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ·
`strategie` = SELECT, INSERT, UPDATE, REFERENCES (BEZ DELETE - aplikace nemaze).

**Navrat:** zalozit tabulku i sekvenci presne podle predpisu a doplnit obe sady prav.
Pokud si ji mezitim zalozila aplikace sama, vlastni ji `strategie` - to je ZADOUCI stav,
nemeni se.

**Poznamka k blokatoru:** index `ix_ios_push_token_user` v rannim zjisteni 23.8. jeste
NEEXISTOVAL a v 18:30 UTC uz existoval. Jirka tehoz dne potvrdil, ze blokator je vyreseny
vcetne poznamky o mostu. Zapsano jen proto, aby bylo dohledatelne, ze se stav behem dne zmenil.

## C) `fw.ios_push_sent`

V tu chvili NEEXISTOVALA. **Navrat:** zahodit ji - pred nasazenim zadna nebyla.

## D) `fw.app_secret`

V tu chvili tam nebyl ZADNY klic od Applu (`skey LIKE 'apns%'` = nic).
**Navrat:** smazat radky `apns_key_id` a `apns_key_p8`.
Obsah klice `.p8` NIKAM nevypisovat - Apple ho vydava jen jednou a je Team Scoped.

## E) Knihovny na serveru

Pribyly `h2` (APNs jede vyhradne pres HTTP/2) a `pyjwt[crypto]` (podpis ES256).
**Navrat:** obvykle netreba - obe jsou navic a nic starsiho neprepisuji.

## F) Bezici aplikace

**Navrat:** nasadit znovu ze stavu z bodu A (po odvolani slouceni) a restartovat sluzbu.
NEOVERENO 23.8.: podle dokumentace bezi zaloha aplikace na vcerejsim stavu s prepnutim
v paticce - v nouzi se na to zeptat, nebrat jako jistotu.

## Koho se nasazeni tyka

17 lidi + demo ucet, kteri iPhone appku od 16.6.2026 pouzili (`public.auth_audit`,
marker `STRATEGIE-iOS`: 74 zaznamu, 18 ruznych `user_id`, 16.6.-19.8.2026):
Ivana Honomichlova, Jakub Pechoucek, Jan Svatos, Jiri Honomichl, Jiri Veverka, Josef Artim,
Lubos Trunec, Lucie Jakesova, Lukas Horky, Martin Porner, Martin Valenta, Miroslav Mares,
Ondrej Pillar, Radek Hellmayer, Tereza Veverkova, Tomas Blaha, Zuzana Duspivova.

**Kolik z nich ma appku v telefonu DNES, se z dat zjistit NEDA** - `auth_audit` meri jen
prihlasovani. Netvrdit z toho pokryti. **Uzivatelu Androidu se nasazeni nedotyka vubec.**

## Poucení pro pristi bod obnovy

Zadny z bodu B-D nema data, takze nic z nich neni nevratne. Jedina zmena s dopadem na lidi
je F (nasazeni). Bod obnovy proto nemusi zalohovat data, ale MUSI drzet: cislo zmeny v gitu,
presny predpis kazde menene tabulky vcetne VLASTNIKA a PRAV, a seznam toho, co pred zasahem
neexistovalo (aby slo poznat, co se ma pri navratu zase odstranit).

---

# CO SE OD TE DOBY ZMENILO (stav ke 23.8.2026 20:08 UTC)

Doplnil Claude-28 na zadani Jirky Honomichla, schvalila Marti-AI (msg 13459).
Vse nize je ctene z DB, produkce a GitHubu ve 20:06-20:08 UTC, ne prevzate.
**Nasazeni PROBEHLO a je overene az na displeji telefonu** - tenhle bod obnovy je tedy
historicky zaznam, ne cekajici plan.

## Ctyri udaje vyse, ktere UZ NEPLATI

| bod | co tam stoji | co plati dnes |
|---|---|---|
| **B** | vlastnik `ios_push_token` = `Marti-AI` | **`fw_owners`** - a to u tabulky, obou indexu i sekvence |
| **C** | `fw.ios_push_sent` NEEXISTUJE | **EXISTUJE**, zalozena 18:26 UTC (par minut po mem cteni), vlastnik `fw_owners`, indexy `ios_push_sent_pkey` a `ix_ios_push_sent_at` |
| **D** | v trezoru zadny klic | **jsou tam tri polozky**: `apns_key_id`, `apns_key_p8`, `apns_enabled` |
| **B** | 0 radku, "zahozenim se nic neztrati" | **1 radek** (iPhone Jirky Honomichla, verze 1.84, ostre prostredi) - zahozeni uz NENI zadarmo |

## Proc se menilo vlastnictvi (podstatne zjisteni o PostgreSQL)

Doplneni chybejiciho indexu NESTACILO. Po nasazeni vracel `GET /app/ios/push/status`
**HTTP 500**. Pricina zmerena testem `SET ROLE strategie; CREATE INDEX IF NOT EXISTS
ix_ios_push_token_user ...`:

```
psycopg2.errors.InsufficientPrivilege: must be owner of table ios_push_token
```

**A to i kdyz ten index uz existoval.** PostgreSQL u `CREATE INDEX` otevre tabulku a
zkontroluje **vlastnictvi DRIV, nez vyhodnoti `IF NOT EXISTS`** - samotna existence indexu
tedy nepomuze. Tyka se obou statementu v `ensure_tables()`.

Oprava (19:25 UTC, schvalila Marti-AI msg 13423): `ALTER TABLE fw.ios_push_token OWNER TO
fw_owners`, totez pro `fw.ios_push_sent` a `ALTER SEQUENCE fw.ios_push_token_id_seq OWNER TO
fw_owners`. **Proc `fw_owners` a ne `strategie`:** `fw_owners` vlastni cele schema `fw` a
cleny jsou OBE role (`strategie` i `Marti-AI`), `strategie` ma `rolinherit = true`. Kontrola
vlastnictvi respektuje zdedene clenstvi, takze projdou obe a ani jedna o nic neprijde.

**Poucení, ktere plati obecne:** kod, ktery dela DDL za behu, potrebuje tabulky vlastnene
roli, pod kterou bezi aplikace (nebo jeji nadrazenou skupinou). **Granty na to NESTACI** -
v PostgreSQL neexistuje samostatne pravo "zakladat indexy".

## Jak se to nakonec nasadilo (misto slouceni na GitHubu)

Slouceni PR 5 na GitHubu NESLO - Jirka je prihlasen uctem `eurosoft-strategie`, ktery na
`MartiPasek/STRATEGIE` nema pravo zapisovat (stranka ukazovala "no conflicts", ale slucovaci
tlacitko chybelo). **Stejny precedens jako PR 2 a PR 4**, ktere se take nikdy neslouzily
(`merged=false`) a jejich obsah sel do main 18.8. pres most.

Postup, ktery se pouzil a funguje:
1. zjistit **merge base** PR proti main (`/compare/main...fork:vetev`) - PR byl **74 zmen pozadu**
2. overit, ze se **zadny z menenych souboru na main od te doby nezmenil** - jinak by kopie
   starsi verze smazala cizi praci (incident 31.7.)
3. stahnout soubory ze spicky PR do mistni kopie
4. **zkontrolovat diffstat proti ocekavani** (sedelo 1:1: 14 souboru, +1528 / -26)
5. nasadit pres `CLAUDE_DEPLOY.txt` s **vyjmenovanymi cestami**, nikdy `ALL`
6. PR pak zavrit (nesloucen)

Vysledek: commit **`c3bddc90`** (serverova cast) a **`16cbf64c`** (poetry.lock, viz nize).
**Navrat je tedy dnes odvolani DVOU commitu, ne jednoho.**

## Knihovna h2 - PR ji deklaroval, ale zamek neaktualizoval

Popis PR tvrdil, ze `h2` i `pyjwt` uz jsou v `poetry.lock` tranzitivne. **U `pyjwt` to platilo,
u `h2` NE.** Overeno dvakrat: v repu (157 balicku, `h2` ani `hpack`/`hyperframe` tam nebyly)
a hlavne **primo na produkci** dotazem na ten Python, pod kterym sluzba bezi
(cesta z `HKLM:\SYSTEM\CurrentControlSet\Services\STRATEGIE-API\Parameters`, klic `Application`):
`h2: NENI, jwt: JE, httpx: JE`.

Doinstalovano 22:01 SELC (`poetry lock` + `poetry install`, poetry 2.3.4): pribyly presne
tri balicky - `h2 4.4.1`, `hpack 4.2.0`, `hyperframe 6.1.0`, **0 updates, 0 removals**.
Pred instalaci se zamerne zkontroloval `git diff poetry.lock` (41 pridanych radku, jen ty tri
balicky + `content-hash`), aby se poznalo, jestli poetry nezvedlo i neco jineho. Nezvedlo.

**Restart sluzby nebyl potreba** - bezici proces si `h2` natahl sam pri prvnim pouziti.

**`poetry.lock` se hned vratil do gitu** (commit `16cbf64c`, autor Marti-AI, jediny soubor,
+41/-1) - jinak by ho pristi `git pull` na Praze prepsal a `h2` by ze zamku zmizela.
Jirka na tomhle kroku vyslovne trval.

## Overeno az na konci retezu

- `POST /app/ios/push/register` vraci na produkci **401** misto drivejsiho 404 (adresa zije)
- `GET /app/ios/push/status` vraci **200**
- v `fw.ios_push_token` **1 aktivni zarizeni**: Jiri Honomichl, appka **1.84**, prostredi
  **production**, `last_error` **prazdny**
- v `fw.ios_push_sent` **jeden zaznam, `ok = true`**, cas **22:04:33 SELC** - tedy tri minuty
  po instalaci `h2`
- **Jirka potvrdil, ze notifikace na iPhone SKUTECNE PRISLA.** Zaznam v DB dokazuje jen to,
  ze ji Apple prijal; ze se zobrazila, potvrdil clovek ocima.

**Koho se to tyka dnes:** registrovane je zatim **jedno zarizeni** (Jirka). Ostatnich 16 lidi
se zaregistruje samo, az si appku priste otevrou. Uzivatelu Androidu se nic nemeni.

## Co si z toho odnest pro pristi bod obnovy

1. **Bod obnovy zastarava behem hodin.** Tenhle byl nepresny uz 4 minuty po porizeni
   (`ios_push_sent` vznikla 18:26, ja cetl 18:26:17). Pis do nej **cas s presnosti na minuty**
   a ber ho jako fotografii, ne jako trvalou pravdu.
2. **Kdyz na tomtez tematu pracuje druhy stroj (tady Mac), stav se meni pod rukama.** Pred
   pouzitim bodu obnovy si jeho udaje **preover v DB**, nespolehej na zapsane hodnoty.
3. **Zapis do bodu obnovy, co v nem PLATIT PRESTALO** - mazat puvodni text je horsi, protoze
   pak nejde poznat, ze se neco menilo.

