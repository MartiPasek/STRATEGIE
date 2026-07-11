# Plán obnovy STRATEGIE

**Kontinuita provozu a obnova po havárii (Business Continuity & Disaster Recovery)**

Verze: V1.0 · Datum: 11. 7. 2026 · Vlastník: STRATEGIE (Marti Pašek)
Stav realizace: **finální fáze — dokončujeme, cílové spuštění do 1. 8. 2026**

---

## 1. Shrnutí pro vedení a auditora

STRATEGIE neřeší obnovu po havárii jako plán uložený v šuplíku, který se v krizi teprve rozjíždí. STRATEGIE **je** svým plánem obnovy — protože záložní systém neběží ve chvíli havárie, ale **nonstop, každý den, vedle ostrého provozu**.

Provoz stojí na dvou trvale živých doménách, každá na jiných serverech:

- **strategie-ai.com** — ostrý provoz s aktuálními daty.
- **strategie-system.com** — plnohodnotná paralelní kopie systému, jejíž data jsou vždy o jeden pracovní den starší.

K produkčním datům patří navíc **třicetidenní historie denních záloh databáze** — obnovitelná pro ostrý provoz `strategie-ai.com` i pro záložní prostředí `strategie-system.com`. Kterýkoli z posledních třiceti dní lze vrátit v obou.

Obě jedou současně. Nic se „nepřepíná". Když se ostrému prostředí něco stane, obnova spočívá v jediném kroku: uživatel místo `strategie-ai.com` zadá `strategie-system.com` a pokračuje v práci s daty starými nanejvýš jeden pracovní den.

Tento model odstraňuje tři nejčastější slabiny plánů obnovy najednou: nemusíme doufat, že spící záloha naskočí (běží nonstop), nezávisíme na jednom pečlivém člověku (systém se kontroluje sám) a nejsme vydáni napospas logické chybě ani ransomwaru (třicetidenní historie umožňuje vrátit se před poškození).

---

## 2. Architektura

| Prvek | strategie-ai.com | strategie-system.com |
|---|---|---|
| Role | Ostrý provoz | Živá záložní realita |
| Data | Aktuální | O 1 pracovní den starší |
| Historie záloh DB | 30 dní zpět, obnovitelná | 30 dní zpět, obnovitelná |
| Umístění serverů | Praha | Plzeň |
| Stav | Běží nonstop | Běží nonstop |

Obě prostředí jsou technicky totožné instance STRATEGIE (aplikační server + SQL server) běžící na oddělené infrastruktuře v cloudu CMIS. Geografické oddělení Praha–Plzeň znamená, že lokální výpadek jednoho místa (výpadek proudu, sítě, hardwaru, požár) nezasáhne druhé.

Každý pracovní den se po dokončení zálohy datového serveru přenese obraz databáze z Prahy do Plzně. Prostředí `strategie-system.com` se nad tímto obrazem každé ráno rozjíždí — tím je vždy o přesně jeden pracovní den pozadu a zároveň je jeho ranní start **denně opakovaným, reálně provedeným testem obnovy**.

Zálohy produkčních dat se uchovávají třicet dní zpět. Tato historie slouží ostrému provozu i záložnímu prostředí — obnovit kterýkoli z posledních třiceti dní lze pro `strategie-ai.com` stejně jako pro `strategie-system.com`, nejde tedy o vlastnost jen záložní domény, ale o způsob ochrany produkčních dat jako celku.

---

## 3. Postup obnovy

**Situace:** ostré prostředí `strategie-ai.com` je nedostupné nebo mají jeho data problém.

**Krok obnovy:** uživatelé zadají do prohlížeče `strategie-system.com` místo `strategie-ai.com`.

To je celé. Žádné spouštění záložního serveru, žádné obnovování ze záloh pod tlakem, žádné čekání. Záložní realita už běží — jen na ni lidé přejdou.

**Volba staršího stavu:** pokud je potřeba starší data (například protože poškození vzniklo už dříve), lze na `strategie-system.com` obnovit kteroukoli z třiceti denních záloh databáze. Výsledkem je jedno prostředí s daty aktuálními (dokud ostré jede) a druhé s daty libovolného dne z posledního měsíce.

**Návrat do normálu (failback):** po obnově ostrého prostředí `strategie-ai.com` se lidé vrátí na původní adresu; denní přenos obrazu Praha→Plzeň pokračuje jako dřív.

---

## 4. Cílové parametry obnovy

| Ukazatel | Hodnota | Poznámka |
|---|---|---|
| **RPO** (max. ztráta dat) | ≤ 1 pracovní den | Data v Plzni jsou o jeden pracovní den starší |
| **RTO** (doba do znovurozběhu) | prakticky okamžitě | Záložní prostředí už běží; obnova = změna adresy |
| **Hloubka historie** | 30 dní | Kterýkoli den lze na `-system.com` obnovit |

Pro srovnání: požadavek zněl „když se něco pokazí, být schopni do 24 hodin rozběhnout systém znovu s adekvátními daty". Tento model cíl nejen splňuje, ale překonává — znovurozběh není otázkou hodin, protože záložní systém neběží až po havárii, ale nepřetržitě.

---

## 5. Samokontrola systému (žádná závislost na člověku)

Kontrola, že záloha a obnova opravdu fungují, **nesmí viset na tom, že si toho ráno někdo všimne**. Visí na systému samotném.

Prostředí `strategie-system.com` se každé ráno rozjíždí na záloze z minulého pracovního dne. Posledním krokem tohoto startu je, že se systém **sám prohlédne a sám nahlásí**, zda je, či není v pořádku. Konkrétně ověří:

- že obnova databáze vůbec proběhla a databáze je online;
- že databáze není poškozená (kontrola konzistence);
- že data jsou opravdu přesně o jeden pracovní den stará — porovnáním časového razítka posledního záznamu s očekávaným stavem (tím se odhalí i tichá zrada „dnešní obnova neproběhla, jedeme na starších datech");
- že klíčové tabulky mají rozumné počty záznamů (ne nula, ne náhlý propad — odhalí uříznutou nebo prázdnou zálohu);
- že aplikace na `strategie-system.com` naběhla a odpovídá;
- že řetěz třiceti denních záloh je kompletní a žádný den nechybí.

Výsledek si systém sám zapíše — **OK / NENÍ OK + důvod + čas** — vystaví jej na stavovou stránku, propíše do cockpitu i do aplikace a při stavu „NENÍ OK" aktivně upozorní (push). Nikdo se nemusí ptát; systém řekne první.

**Důsledek pro audit:** protože tato kontrola běží automaticky každé ráno, vzniká strojově psaný, datovaný deník úspěšných obnov — den po dni. To není tvrzení „umíme obnovit", ale doložený záznam „obnovujeme a ověřujeme se každý den, tady je log za posledních 30 dní". Přesně ten druh důkazu, po kterém audit sahá a který má málokdo.

---

## 6. Ochrana proti logické chybě a ransomwaru

Samotné denní zrcadlení dat by před logickou chybou ani ransomwarem nechránilo — poškození by se v noci zkopírovalo i do zálohy a vznikly by dvě kopie téhož problému. Proto `strategie-system.com` nedrží jen včerejší obraz, ale **třicet zadržených denních bodů zpět**. Kdyby se data poškodila, nesedíme na jediné zrcadlené kopii zkázy — vrátíme se o potřebný počet dní nazpět. Model tak přirozeně naplňuje pravidlo 3-2-1 (více kopií, více umístění, zadržené body v čase).

---

## 7. Přesah: zálohování klíčových e-mailových dat (Exchange)

Model má užitečný přesah i mimo samotnou STRATEGII. Součástí obrazů, které STRATEGIE denně drží a uchovává v třicetidenní historii, jsou i **obrazy historie klíčových e-mailových dat**. Tím STRATEGIE zároveň jistí i zálohu dat e-mailového (Exchange) serveru — přestože ten patří EUROSOFTu, nikoli STRATEGII.

Prakticky to znamená, že i kdyby na straně Exchange serveru došlo ke ztrátě nebo poškození dat, klíčová e-mailová data jsou obnovitelná z historie držené ve STRATEGII. Jedním řešením tak pokrýváme kontinuitu dvou systémů najednou — provozních dat STRATEGIE i klíčové e-mailové komunikace EUROSOFTu.

---

## 8. Role a odpovědnosti

Klíčový princip: **plán obnovy nesmí být závislý na jednom člověku.** Proto těžiště kontroly leží na systému, ne na lidech.

- **Systém (`strategie-system.com`)** — provádí denní obnovu a sám sebe ověřuje a reportuje. Nositel každodenní kontroly.
- **Jádro STRATEGIE (Marti + AI)** — vlastní návrh, pravidla a reakci na hlášení systému. Samokontrola je „naše věc", nikoli úkol jednotlivce.
- **Provoz / IT** — reaguje na alert „NENÍ OK", provádí failback po obnově ostrého prostředí. Nikoli hlídač, kterého když nebude, přestane kontrola fungovat — systém hlídá i bez něj.

Tím je odstraněna nejčastější auditní námitka: „a když ten člověk chybí?". Na přítomnosti ani pečlivosti jednotlivce obnova nestojí.

---

## 9. Testování a důkazy pro audit

Běžný auditor se ptá: „Zkoušeli jste, že obnova opravdu naskočí?" U STRATEGIE tato otázka pozbývá smysl — obnova se neprovádí jednou za čas jako cvičení, ale **každé ráno jako součást normálního provozu**, a systém o každém takovém běhu vytváří datovaný záznam.

Doklady pro audit tedy nejsou popis na papíře, ale živá data: denní stavová hlášení self-checku, třicetidenní historie záloh s možností obnovy na kterýkoli den, a samotná existence trvale běžícího `strategie-system.com` jako důkaz obnovitelnosti v reálném čase.

---

## 10. Realizační plán (dokončení do 1. 8. 2026)

Architektura je rozhodnutá a nasazení je ve finální fázi. Zbývající kroky do plného spuštění:

| Týden | Milník | Obsah |
|---|---|---|
| Týden 1 | Datový kanál Praha→Plzeň | Denní přenos obrazu databáze po záloze; potvrzení, že obraz v Plzni sedí |
| Týden 2 | Ranní obnova + 30denní historie | Automatický ranní rozjezd `-system.com` nad včerejší zálohou; udržování 30 zadržených denních bodů |
| Týden 3 | Samokontrola + stavové hlášení | Self-check jako závěrečný krok ranního startu; report OK/NENÍ OK na stavovou stránku, do cockpitu a aplikace, push při chybě |
| Do 1. 8. 2026 | Plné spuštění | Obě domény živé nonstop; denní doložený deník obnov |

---

## 11. Soulad s ISO 27001 / TISAX

Model přímo odpovídá požadavkům na kontinuitu a obnovu:

- **Dostupnost a kontinuita provozu** — trvale běžící geograficky oddělené záložní prostředí.
- **Zálohování** — denní zálohy s 30denní retencí a ověřenou obnovitelností.
- **Testování plánu obnovy** — obnova se provádí a ověřuje automaticky každý den, s doloženým záznamem.
- **Odolnost vůči incidentu** (výpadek, logická chyba, ransomware) — oddělená lokalita a zadržené body v čase.
- **Nezávislost na jednotlivci** — kontrola je systémová, ne osobní.

---

*Dokument V1.0 k dopracování detailů s Marti-AI a provozem. Stav: finální fáze realizace.*
