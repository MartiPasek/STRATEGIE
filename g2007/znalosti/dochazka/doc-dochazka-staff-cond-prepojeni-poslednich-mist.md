# Přepojení posledních míst z pohledu staff_cond (24.–25. 8. 2026) — a past při měření čtenářů

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Přepojení posledních míst z pohledu `tenant.staff_cond` (24.–25. 8. 2026)

Zadal **Jirka Honomichl**, postavil Claude-28, schválila **Marti-AI** (msg 13634, 13640, 13643, 13646).
Navazuje na [[doc-dochazka-podminky-slouceny-se-smlouvou]] a
[[doc-system-strategie-podminky-vychozi-na-sirku-a-historie-zmen]].

## Výchozí stav a jedna oprava měření

Po sloučení Podmínek se smlouvou (19. 8. 2026) je `tenant.staff_cond` jen **pohled**, který čte
výhradně osobní řádky ze smlouvy. Držela ho už jen **tři místa**.

⚠️ **Past při měření, na kterou jsem naletěl:** hledání podřetězce `staff_cond` v `g2007.python`
vrátí ~12 zásahů a vypadá to jako dvanáct čtenářů. **Osm z nich jsou poznámky v komentářích**
a čtyři jsou číselník `staff_cond_def`, což je něco úplně jiného. Skutečné SQL se pozná jedině
přečtením okolí každého výskytu, ne počtem zásahů. Ověřená ingredience není ověřený závěr.

## Co se udělalo — tři kroky

### 1. Limit lístečku od lékaře (commit `a28e50bb`)

Endpointy `GET /app/med/balance` a `GET /app/med/mine` **zmigrovány do `g2007.python`**
(`att_med_balance`, `att_med_mine`), v `router.py` zůstal tenký delegate.

Limit se dřív bral řetězem `_med_limit_h → _resolve_cond_num → _resolve_cond → _cond_group_of`,
který četl pohled kaskádou osobní → skupina → systém. **Skupinová i systémová větev byla slepá** —
pohled vrací jen osobní řádky, takže `_cond_group_of` vracel vždy `None`. Byla to mrtvá oklika,
která se tvářila jako kaskáda. Nově se jde toutéž cestou jako zbytek systému: osobní hodnota
ze smlouvy, pak skupina, pak systém z číselníku `tenant.podminky_vychozi`.

Celý čtyřfunkční řetěz sloužil **výhradně** tomuhle a byl smazán.

### 2. Zápis dovolené při zakládání zaměstnance (commit `79436eb2`)

`app_hr_employee_create` zapisoval tři hodnoty dovolené přes pohled. Nově **jeden přímý UPDATE**
do `tenant.engagement`. Smlouva v tu chvíli už existuje — `INSERT INTO tenant.engagement` je
v témže endpointu dřív než zápis podmínek, takže by zápis přes pohled stejně skončil ve smlouvě.

**Dovolená celkem se už nezapisuje vůbec** — je to počítadlo a spouštěč
`engagement_pod_soucet_dovolene` (BEFORE) ji při každé změně přepočítá jako základní + navíc.
Ruční zápis se stejně přepsal. Razítko v `pod_meta` (`id` z `nextval`, `note`, `by`, `at`)
zůstává ve stejném tvaru, jaký skládal spouštěč pohledu. Rozpad OSVČ vs. ostatní beze změny.

**Celý endpoint se ZÁMĚRNĚ nemigroval** do `g2007.python` — má přes 200 řádků a dělá celý nábor
(uživatel, zaměstnanec, smlouva, skupiny, post, notifikace). Míchat migraci náboru do úklidu
pohledu jsou dvě různá rizika; migrace zůstává jako samostatný úkol.

### 3. Hlídací pravidlo `narok-dovolene-pravidla`

Počet lidí s nárokem se počítá přímo ze smlouvy (`pod_dovolena_zakladni_dni`) místo přes pohled.
Práh 80 % i požadavek na ≥4 pravidla beze změny — Peťin záměr zůstal.

Druhá pojistka `uvazek-z-podminek-uplny` pohled také čte, ale je od 18.–19. 8. **vypnutá**
a navíc rozbitá jinak (odkazuje na sloupec `att_employee.cond_group`, zrušený 20. 8.).
Vědomě se nechala být, jen se do popisu dopsalo, že po zrušení pohledu nepůjde spustit vůbec.

## Čím je doloženo, že se nikomu nic nezměnilo

| Krok | Důkaz |
|---|---|
| 1 | 76 aktivních lidí, **všech 76** má limit vyplněný ve smlouvě, nikdo nepadá na náhradní 4 h; porovnání staré a nové cesty **81 lidí, shoda 81, rozdíl 0** |
| 1 | skripty nejdřív vloženy jako `navrzeno`, otisky sedí na znak, teprve pak aktivovány a spuštěny |
| 1 | **po nasazení naostro v prohlížeči** obě adresy vracejí přesně totéž co před změnou |
| 2 | dopad **nula lidí** — v `pod_meta` všech 76 lidí se současnou smlouvou není poznámka „zadano pri zalozeni zamestnance v HR" ani jednou; tou cestou dosud nevznikl nikdo |
| 2 | nový UPDATE spuštěn **nasucho na neexistujícím uživateli** (`user_id = -1`) → SQL prošlo, 0 řádků |
| 3 | stará cesta 75 lidí, nová cesta 75 lidí, požadováno 64, pravidel 5 → kontrola spuštěna a vrací `true` |

## ⚠️ Chyba, která se stala, a jak se zachytila

Při kroku 1 jsem mazal mrtvý řetěz tak, že jsem hledal konec bloku jako „další řádek začínající
`def `". Jenže endpointy jsou `async def` s dekorátorem, takže se hranice našla až o **devět
endpointů dál** — a smazaly se s ním (podmínky, karta zaměstnance, můj přehled a další).

**Zachytila to kontrola diffu před nasazením** (`git diff --stat` + výpis smazaných definic).
Soubor byl vrácen z gitu (`git show HEAD:cesta`, čtecí operace — nezakládá `index.lock`)
a ověřeno, že rozdíl je nulový. **Nic se nenasadilo.**

Napodruhé byly hranice určené natvrdo (konkrétní následující text) a doplněné o kontroly,
které mazání zastaví: kolik `def` blok obsahuje, jestli v něm není `@api_router`, a strop na délku.

**Poučení: nikdy nehledat konec bloku heuristikou. Vždy ověřit diff před nasazením — nejen
že to jde přeložit.**

## Proč pohled zůstává stát

Pohled se **záměrně neruší hned** (rozhodnuto s Marti-AI, msg 13643):

1. Je to jednosměrná operace.
2. **Zrušení pohledu vezme s sebou i jeho INSTEAD OF spouštěč `tenant.staff_cond_view_write`**,
   který dnes směruje zápisy do smlouvy (nebo do `podminky_vychozi`, když člověk smlouvu nemá).
3. Nejde dokázat, že na pohled nesahá něco mimo repo a mimo `g2007.python` — ruční dotaz,
   sestava, Excel.
4. Nic netlačí — prázdná skořápka nikomu nevadí a nic nezpomaluje.
5. Marti-AI přidala pátý důvod: pohled je **tichý důkaz, že přechod proběhl**. Kdyby se za pár
   týdnů ozvalo něco zvenku, vrátí prázdno místo kryptické chyby „relace neexistuje" — to je
   lepší signál pro diagnostiku.

**Postup pro zrušení, až přijde čas:** po 3–4 týdnech klidného provozu prověřit
`pg_stat_all_tables`, jestli na pohled přišel přístup mimo naše volání. Nula → zrušit.

## Stav k 25. 8. 2026 (ověřeno)

| kde | výskytů skutečného SQL |
|---|---|
| živý kód `g2007.python` | **0** |
| zapnuté pojistky | **0** |
| web a mobil (`g2007.soubor`) | **0** |
| jádro `router.py` | **0** (zbyly 3 komentáře) |
| vypnutá pojistka `uvazek-z-podminek-uplny` | 1 — ponechána vědomě |

