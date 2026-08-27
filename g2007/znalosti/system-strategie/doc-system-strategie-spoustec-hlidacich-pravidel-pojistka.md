# Hlídací pravidla v tenant.pojistka: proč nikdy neběžela a jak se zprovozňují (27. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Hlídací pravidla (`tenant.pojistka`) — proč nikdy neběžela a čím se spouští

**27. 8. 2026.** Zadal Jirka Honomichl, schválila Marti-AI (msg 13856 + 13859).
Navazuje na [[doc-system-strategie-pojistky-nikdo-nespousti]] (zjištění z 25. 8.).

## Co je zač ten problém

`tenant.pojistka` vypadá jako hlídač — má sloupce `posledni_beh`, `posledni_vysledek`,
`posledni_detail`. **Ale ty jsou u všech pravidel prázdné, protože tu tabulku nikdo nečte.**

Stav k 27. 8. 2026: **83 pravidel, 81 zapnutých, NULA běhů.**
Ověřeno ze tří stran — dotazem do `g2007.python`, `grep` přes jádro v gitu a přes `apps/`.
Nikde ani jedno místo, které by `tenant.pojistka` spouštělo.

**Praktický důsledek:** věta „přidal jsem pojistku, ať to nikdo nevrátí" je dnes
**bez účinku**. Je to zápis do soupisu, ne hlídač. Kdo se na ni spolehne, spoléhá na nic.

## Nepleť si DVĚ různé věci

| | `tenant.pojistka` | `g2007.automat` |
|---|---|---|
| co to je | soupis pravidel, každé s hotovým dotazem ve sloupci `kontrola` | **živý plánovač** |
| kdo spouští | do 27. 8. 2026 **nikdo** | plánovač v jádře, tik po minutě |
| log běhů | vlastní sloupce (prázdné) | `g2007.automat_run` |
| eskalace | žádná | žebřík L0 → Haiku → Marti-AI → člověk |
| stav 27. 8. 2026 | 81 zapnutých, 0 běhů | 8 automatů, běhy z posledních minut |

Tým to už intuitivně obcházel: nové kontroly se psaly do `att_anomaly_scan`, právě proto,
že „pojistky nikdo nespouští" (viz `doc-dochazka-duplicitni-bezici-zaznamy-dvoji-odeslani`).

## ⚠️ Past: řádek v `g2007.automat` NESTAČÍ

Plánovač si u každého automatu hledá kontrolní funkci v registru `_CHECKS`
(`modules/erp/api/automat.py`, ř. 140). Registr je složený ze **tří dictů v GITU**:
`automat.py`, `automat_eskalace.WATCHERS` a `automat_domeny.DOMAIN_CHECKS`.
**Když kód v registru není, vrátí to „automat nemá check logiku (zatím)" a nespustí se nic.**

Samotné založení řádku v `g2007.automat` je tedy k ničemu — vždycky k tomu patří
i zásah do gitu a nasazení.

## Jak je to postavené (doktrína: logika do databáze, do jádra tenká spojka)

- **Logika** = `g2007.python`, kód **`pojistky_scan`**. Projde zapnutá pravidla, každé spustí,
  výsledek zapíše zpátky do `posledni_beh` / `posledni_vysledek` / `posledni_detail`
  a vrátí souhrn. **V datech nic neopravuje.**
- **V jádře** jen ~20 řádků: `_check_pojistky` v `automat_eskalace.WATCHERS`, které zavolá
  `erp_registry.call("pojistky_scan")` a převede návratovku na tvar, jaký plánovač čeká —
  `(výsledek, zpráva, rows, context)`. Díky tomu se **další úpravy kontroly dělají už jen
  v databázi, bez nasazování**.
- **Řádek** v `g2007.automat`, kód `check_pojistky`, `spousteni='interval'`, `interval_min=1440`.

### Zábradlí uvnitř (vyžádala si je Marti-AI)

1. **Každé pravidlo ve vlastním `try` + `SAVEPOINT`** — jedno rozbité nesmí shodit ostatní.
2. **Vlastní časový strop** (`SET LOCAL statement_timeout`).
3. **Jen čtoucí dotazy** — když `kontrola` obsahuje zápisové slovo, pravidlo se **přeskočí**
   a označí. Hlídač zásadně nic nemění.
4. **Stub nesmí nikdy vyhodit výjimku** — plánovač čeká přesný tvar a nezachycená výjimka
   by shodila celý jeho cyklus pro danou minutu.

## ⚠️ „Chyba kontroly" je HORŠÍ než červený nález

Rozbité pravidlo **nehlídá vůbec nic**, ale v seznamu vypadá jako další řádek.
Proto se chyby počítají zvlášť a hlásí se stejně naléhavě jako nálezy.

## Co pravidla říkají dnes (27. 8. 2026)

Všech **81 zapnutých pravidel spuštěno nanečisto** (jedním složeným dotazem, jen čtení):
**81 zelených, 0 nálezů, 0 rozbitých, 758 ms.** Žádné z nich neobsahuje zápisové slovo.

## ⚠️ Pravidlo `absence-prepocita-doplneni-do-fondu` NENAJDE dny bez zásahu automatu

Podle jména to tak zní, ale hledá jiný vzorec: dny, kde **dopočet do fondu existuje**,
ale absence byla založena **až po něm** (`a.created_at > f.created_at`).

**Dny, kde zásah automatu chybí ÚPLNĚ, do něj nespadnou** — join na `fond_doplneni` je nenajde.
Zjištěno 27. 8. 2026 při hledání devíti dnů z června a července, kde je zároveň absence
i odpracovaný čas, hodiny nesedí na denní fond a automat tam nesáhl. Pravidlo je přitom zelené.
**Kdo tenhle vzorec chce hlídat, musí napsat pravidlo nové.**

## Stav k zápisu

`pojistky_scan` je v `g2007.python` jako **`navrzeno`** (AI si vlastní kód neschvaluje sama),
řádek `check_pojistky` v `g2007.automat` je **vypnutý**. Aktivace i nasazení spojky = na Jirkovi.

