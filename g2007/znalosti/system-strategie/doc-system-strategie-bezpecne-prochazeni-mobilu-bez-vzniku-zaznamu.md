# Jak bezpecne projit vsechny obrazovky mobilu, aniz vzniknou zaznamy v ostrych datech

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Bezpecne prochazeni mobilni appky (kontrola vzhledu na vsech obrazovkach)

**Vzniklo 31. 8. 2026** pri plosne kontrole, jestli spodni lista nekde neprekryva obsah.
Zadal Jirka Honomichl ("proklikej to s mym prihlasenim a vznikle zaznamy po sobe smaz"),
provedl Claude-28. Prochazi se **pod prihlasenim ziveho cloveka v ostrem provozu**,
takze hrozi, ze samotne prochazeni neco zalozi.

## Zaver: nic mazat nemusis, kdyz to udelas takhle

Prochazeni **samo o sobe zadny zaznam nezaklada** - zapisuje se az akci uzivatele (tlacitko).
Ale nespolehej na to, **dolozit se to musi**. Dva nezavisle dukazy:

### 1) Odposlech v prohlizeci (pojistka pred akci)

Obal `window.fetch` a zaznamenej vse, co neni `GET`/`HEAD`. Blokuj jen zjevne destruktivni
(`DELETE`, nebo URL/telo obsahujici `delete|smaz|remove|storno`), zbytek **propust a zaloguj**.

⚠️ **KLICOVA PAST: appka cte data pres `POST`.** Vetsina obrazovek si data tahne pres
`POST /api/v1/erp/app/erp_registry/run` s telem `{"kod":"...","args":[...]}`. To **NENI zapis**.
Kdo zablokuje vsechny `POST`, **rozbije nacitani dat** - obrazovky se zaseknou na prazdnem stavu
a mereni vzhledu pak nic neznamena (stalo se, prvni pokus jsem musel zahodit).

Pri pruchodu vsech 131 obrazovek se zachytilo **5 nezapisovych volani** - vsechna jen cetla
(`erp_registry/run` pro seznam lidi a `payslip` s prazdnym PINem). Nic destruktivniho.

⚠️ Kdyz uz obal nasadis, **nesahej na `XMLHttpRequest.prototype.send`** bez ulozeni originalu -
prepsanim bez zalohy si rozbijes druhy komunikacni kanal a musis obnovit stranku.

### 2) Kontrola v datech (dukaz po akci)

Po skonceni se **zeptej databaze**, jestli neco vzniklo. Tabulky, ktere maji `created_at`,
najdes takto:

    SELECT table_schema, table_name FROM information_schema.columns
    WHERE table_schema IN ('tenant','public') AND column_name = 'created_at'
      AND (table_name LIKE 'att%' OR table_name LIKE '%zadost%' OR table_name LIKE '%request%'
           OR table_name LIKE '%notif%' OR table_name LIKE '%task%');

Pak spocitej pribytky za dobu session. **Nestaci pocet - podivej se, CI ty zaznamy jsou.**
31. 8. 2026 pribylo 30 radku v `tenant.att_entry`, ale vsechny patrily lidem, kteri to dopoledne
normalne pichali (Artim, Svenda, Perina, Reitmaier a dalsi) - **ani jeden nevznikl prochazenim.**
Stejne tak 6 radku v `tenant.notification_log` byly cizi (schvalovaci vyzvy jineho okna
a systemove hlaseni o restartu API).

## Jak obrazovky prochazet

- Seznam obrazovek: `Object.keys(window.__M2W.SCREENS)` (k 31. 8. 2026 jich je **131**).
- Prepinani: `window.__M2W.go('<nazev>')`, pred tim `window.__M2W.stack = ['home']`.
  **Je to bezpecnejsi nez klikani mysi** - nemuzes omylem trefit akcni tlacitko
  (napr. chipy u sick day odesilaji zadost hned pri kliknuti).
- **Nemackej nic** - jen zobrazuj.

⚠️ **Nektere obrazovky renderuji dlouho a zablokuji vlakno** (`doc_gen`, `wage_cmp`,
`planapprovals`, `isds`, `sdileny`) - volani nastroje pak spadne na timeout, i kdyz smycka bezi dal.
Osvedcilo se: **spustit pruchod na pozadi** (bez cekani na dokonceni) a jen periodicky odecitat
vysledky, prubezne je ukladat do `localStorage` a po pripadnem obnoveni stranky nacist zpatky
a pokracovat od nedokoncenych. Bez toho ztratis vysledky pri kazdem zaseknuti.

⚠️ **Prohlizec neda precist celou stranku `/mobile` pres `fetch` z konzole** - nastroj to odmitne
(stranka nese prihlasovaci data). Statickou analyzu obsahu delej **z databaze**
(`g2007.soubor`, kod `apps/api/static_db/mobile.html`), ne z prohlizece.

## Uklid po sobe

- Smaz vlastni klice z `localStorage` a **obnov stranku** - tim zmizi odposlech i pomocne funkce.
- Vizualni zvyrazneni (obrysy, prubeznost listy) se nikam neuklada, ale stejne stranku obnov.

## Souvisejici

Pasti pri samotnem MERENI prekryvu (orezani posuvnym rameckem, prvky cele pod listou,
mereni v neustalenem stavu, kontrolni vzorek) jsou u tematu spodni listy:
[[doc-system-strategie-mobil-navh-spodni-lista]]

