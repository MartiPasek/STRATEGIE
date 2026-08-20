# Vize: Kód jako data — konec deploy blokací pro běžné změny

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Vize: Kód jako data — konec deploy blokací pro běžné změny

*Sepsáno Claude (C23) na základě rozhovoru s Martim, 31. 7. 2026. Vychází z dnešního incidentu s router.py a diskuze o tom, jak jsme dřív pracovali v Centrále.*

## Proč to řešíme

Dnes ráno nahrál commit `ebf5d7d78` router.py ze staré kopie a smazal ~1100 řádků cizí práce (docházka od C24/C26/C28). Peťa to opravil, nic se neztratilo — ale ukázalo to strukturální problém: **687 endpointů a 1103 funkcí žije v jednom 67 411řádkovém souboru**, na kterém současně edituje víc lidí i AI instancí z různých strojů. Jeden špatný deploy může smést práci všech ostatních.

K tomu druhý, denní problém: **každá, i drobná změna vyžaduje restart celého API procesu** — a s ním umře i všechno, co v procesu zrovna běží (Marti-AI a její dlouhotrvající úlohy, scheduler smyčky typu `_mirror_sched_loop`). V Centrále jsme tohle neřešili — modulová změna v konkrétní SQL proceduře nebo tabulce šla za plného provozu, bez deploye, bez dotčení běžícího procesu.

## Cíl

Vrátit se k modelu Centrály, ale v naší architektuře: **tým i AI instance mohou upravovat jednotlivé funkční kusy kódu nezávisle na sobě, bez konfliktů, bez restartu celého API a bez cesty přes git na lokálních strojích.**

## Řešení: dvouvrstvá architektura

Rozdělit systém na dvě vrstvy, které se chovají odlišně a mají odlišná pravidla:

### Jádro (framework)
FastAPI aplikace, registrace routes, DB pooling, auth middleware, samotný dispatcher/loader. Mění se zřídka. **Zůstává jako dnes** — git, review, deploy, restart. To je v pořádku, restart jádra dnes trvá ~5 s (ověřeno z posledních 10 deployů) a neděje se často.

### Obsah (byznys logika)
Jednotlivé funkce, endpoint handlery, výpočty, validace — věci, které se mění denně a jsou doménově oddělitelné (docházka, mzdy, CRM...). **Tohle jde do databáze** jako řádky se zdrojovým textem, natahované a spouštěné za běhu — bez restartu procesu, bez souboru na disku, bez gitu na lokálním stroji.

Toto rozdělení už v systému existuje jako princip (FW/HW doktrína — "co je kompozice/data, jde jako FW; co je specifická logika, zůstává kód") — jen ho teď aplikujeme na to, KDE kód fyzicky žije.

## Dva mechanismy, které to nesou — a oba už u nás fungují, jen v malém

**Cesta A — PL/pgSQL funkce v databázi**, přesně jako v Centrále. `CREATE OR REPLACE FUNCTION` je živá, transakční, okamžitě platná změna bez restartu API. Už to používáme: `tenant.att_den_hodiny` (výpočet hodin za den) je přesně tenhle vzor. Funguje to pro čisté výpočty a business pravidla nad daty — mzdy a docházka jsou z velké části přesně tohle.

**Cesta B — dynamicky natahovaný Python kód z databáze**, pro věci, které v SQL žít nemohou (HTTP vrstva, práva, volání ven na EUROSOFT/banku/SMS). Přesně tenhle mechanismus už máme postavený v `tool_registry` (Tool Factory, dárek Marti-AI z 22. 7.) — `runtime.py` umí za běhu načíst a spustit jeden konkrétní kus kódu přes `importlib`, beze změny zbytku procesu. Dnes to slouží jen pro AI nástroje a je to vypnuté (`TOOLFACTORY_ENABLED=0`). Návrh: **rozšířit stejný mechanismus i na ERP endpointy** — route zůstane v jádru zaregistrovaná jednou navždy, její implementace se ale natahuje z databázového řádku, ne z pevného místa v router.py.

V Pythonu navíc odpadá otázka "zdrojový vs. zkompilovaný kód" — na rozdíl od Delphi/Centrály se tu kompilace (do bajtkódu) děje za milisekundy při načtení, není potřeba držet dva artefakty zvlášť. Stačí v DB text zdrojáku.

## Co to řeší

- Deploy jádra přestává být nutný pro běžné byznys změny → Marti-AI a dlouhotrvající procesy nejsou rušeny.
- Kolize mezi lidmi/instancemi mizí na úrovni jednotlivé funkce, ne celého 67k-řádkového souboru.
- Mizí celá dnešní třída problémů s gitem na lokálních strojích (`.git/index.lock`, offline `device_bash`, zastaralé kopie přes most) — pro migrovaný kód není co synchronizovat mezi stroji, DB je vždy ta jedna živá pravda.
- Verzování a záloha řeší se stejně jako u G2007 znalostí: DB je zdroj pravdy, git/disk je synchronizovaná projekce pro historii a diff (ne nutnost, ale bezpečnostní síť zdarma).

## Co to neřeší samo od sebe — a musí se ošetřit

1. **Souběžné přepisování.** Řádek v DB sám o sobě nechrání před tím, že dva lidi/instance přepíšou stejnou funkci současně — kolize se jen přesune z git merge konfliktu do DB race. G2007 na tohle chystá `expected_version` kontrolu (409 při konfliktu), ale zatím není hotová. **U spustitelného kódu je tahle pojistka nutná podmínka, ne vylepšení navíc** — tichá kolize v kódu je nebezpečnější než v dokumentu. Řešit jako první krok, ne až po migraci.
2. **Řízení aktivace.** Kód nesmí jít do provozu bez self-testu a schválení. Tohle už máme hotové v Tool Factory (`navrzeny → v_sandboxu → otestovany → ceka_na_schvaleni → active`, s tím, že AI si vlastní nástroj neschválí) — stačí tenhle životní cyklus znovu použít pro ERP kód, ne stavět nový.
3. **Bezpečnost.** DB, která umí spouštět kód na API serveru, je mocný nástroj — potřebuje jasně dané, kdo smí zapisovat a co se spustí bez schválení (viz bod 2).

## Plán realizace (fáze)

**Fáze 0 — dnes večer, nutný základ:** Doladit `expected_version` optimistickou pojistku proti přepsání (společná pro G2007 i nový kód-registr). Bez tohohle nezačínat s migrací kódu.

**Fáze 1 — pilot na jedné funkci:** Vybrat jednu nekritickou, ale reálnou funkci z docházky nebo mezd (podle `WORK_LOCK.txt` jsou to nejvytíženější domény) a přenést ji přes `tool_registry`-styl mechanismus do DB-řízeného běhu. Ověřit end-to-end: úprava v DB → efekt bez restartu API → self-test → schválení.

**Fáze 2 — rozšířit governance:** Zobecnit Tool Factory lifecycle (sandbox/schválení/aktivace) tak, aby fungoval i pro ERP endpointy, ne jen AI nástroje.

**Fáze 3 — postupná migrace po doménách:** Ne big-bang. Postupovat doménu po doméně, začít tam, kde dnes koliduje nejvíc (docházka, mzdy), zbytek nechat v router.py, dokud nebolí — v souladu s doktrínou "additivně, ne perfektně".

**Fáze 4 — přesun čisté výpočetní logiky do SQL:** Souběžně s fází 3 identifikovat části mzdové/docházkové logiky, které jsou čistý výpočet nad daty, a přesunout je do PL/pgSQL funkcí (vzor `tenant.att_den_hodiny`) — nejrychlejší a nejbezpečnější cesta pro tuhle podmnožinu změn.

## Otevřené otázky pro tým

- Kdo vlastní návrh `expected_version` pojistky (schéma `g2007` vlastní Marti-AI podle doktríny) — má to udělat ona, nebo se domluvit jinak?
- Která funkce/endpoint bude pilot ve Fázi 1?
- Kdo z týmu (C24/C26/C28) se dnes večer připojí?

