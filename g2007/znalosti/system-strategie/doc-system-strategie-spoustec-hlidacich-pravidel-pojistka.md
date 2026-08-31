# Hlídací pravidla (tenant.pojistka) — čím se spouští a komu chodí nálezy (ZAPNUTO 28. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hlídací pravidla (`tenant.pojistka`) — proč nikdy neběžela a čím se spouští

**27. 8. 2026.** Zadal Jirka Honomichl, schválila Marti-AI (msg 13856 + 13859).
Navazuje na [[doc-system-strategie-pojistky-nikdo-nespousti]] (zjištění z 25. 8.).

> ## ✅ ZAPNUTO A OVĚŘENO 28. 8. 2026
>
> Sekce „Stav k zápisu" dole říkala, že `pojistky_scan` je `navrzeno` a `check_pojistky` vypnutý.
> **To už neplatí.** Rozhodl Jirka Honomichl 28. 8. 2026, schválila Marti-AI (msg 13950):
>
> - `g2007.python` **`pojistky_scan`** → `active`
> - `g2007.automat` **`check_pojistky`** → zapnutý, interval **1440 min** (jednou denně)
> - spojka `_check_pojistky` nasazena (commit **`5c247bc8`**)
> - **první ostrý běh 28. 8. 2026 v 10:27:06** — 88 pravidel, 499 ms,
>   **88 v pořádku, 0 nálezů, 0 rozbitých**
>
> **Nálezy se rozesílají podle působnosti** (doplněno 28. 8. 2026 odpoledne, rozhodl Jirka
> Honomichl, schválila Marti-AI msg 13959). Každé pravidlo má sloupec `tenant.pojistka.oblast`,
> adresáta nese číselník **`tenant.pojistka_oblast`** (kod, nazev, email) — mění se jedním
> zápisem do tabulky, **bez nasazování**. Rozdělení k 28. 8. 2026:
>
> | oblast | komu | pravidel |
> |---|---|---|
> | `dochazka` | Petra Šafránková | 48 |
> | `mzdy` | Petra Šafránková | 18 |
> | `vyroba` | Dušan Havlát | 12 |
> | `technicke` | Jiří Honomichl | 7 |
> | `hr` | Šárka Novotná | 4 |
>
> Skript `pojistky_scan` vrací rozpad v `context["podle_oblasti"]` **i s adresátem**;
> spojka `_l3_podle_oblasti` pošle každé oblasti **jen její nálezy** a oblast bez nálezů
> přeskočí. Když oblast v číselníku chybí, jde na zálohu (`_L3_PRIJEMCE`, dnes Jirka)
> a zapíše se to do auditu. Automat, který v mapě není, jde dál původní cestou
> (m.pasek + cc k.ksirova) — `check_service_down` ani `check_backup_freshness` se nezměnily.
>
> **Proč ne do fronty k vyřízení:** `tenant.att_anomaly` má `employee_id NOT NULL` a nese
> dvojici člověk + den (ověřeno na všech 1018 záznamech — jsou to nálezy typu „Novák má
> 12. 8. dlouhou směnu"). Pravidlo z `tenant.pojistka` vrací jen ano/ne — nemá koho ani
> který den do fronty zapsat. Docházkové nálezy pro lidi tam dál chodí z jiného automatu.

## Co je zač ten problém

`tenant.pojistka` vypadá jako hlídač — má sloupce `posledni_beh`, `posledni_vysledek`,
`posledni_detail`. **Ale do 27. 8. 2026 byly u všech pravidel prázdné, protože tu tabulku
nikdo nečetl.**

Stav k 27. 8. 2026: **83 pravidel, 81 zapnutých, NULA běhů.** Ověřeno ze tří stran — dotazem
do `g2007.python`, `grep` přes jádro v gitu a přes `apps/`. Nikde ani jedno místo, které by
`tenant.pojistka` spouštělo.

**Praktický důsledek:** věta „přidal jsem pojistku, ať to nikdo nevrátí" byla **bez účinku**.
Zápis do soupisu, ne hlídač. Kdo se na ni spolehl, spoléhal na nic.
Závazné pravidlo z toho: [[doc-system-g2007-nerikat-pridal-jsem-pojistku-bez-spousteni]].

## Nepleť si DVĚ různé věci

| | `tenant.pojistka` | `g2007.automat` |
|---|---|---|
| co to je | soupis pravidel, každé s hotovým dotazem ve sloupci `kontrola` | **živý plánovač** |
| kdo spouští | do 27. 8. 2026 **nikdo**; od 28. 8. 2026 automat `check_pojistky` | plánovač v jádře, tik po minutě |
| log běhů | vlastní sloupce (od 28. 8. vyplněné) | `g2007.automat_run` |
| eskalace | žebřík přes `check_pojistky` | žebřík L0 → Haiku → Marti-AI → člověk |

Tým to už intuitivně obcházel: nové kontroly se psaly do `att_anomaly_scan`, právě proto, že
„pojistky nikdo nespouští" (viz `doc-dochazka-duplicitni-bezici-zaznamy-dvoji-odeslani`).

## ⚠️ Past: řádek v `g2007.automat` NESTAČÍ

Plánovač si u každého automatu hledá kontrolní funkci v registru `_CHECKS`
(`modules/erp/api/automat.py`, ř. 140). Registr je složený ze **tří dictů v GITU**:
`automat.py`, `automat_eskalace.WATCHERS` a `automat_domeny.DOMAIN_CHECKS`.
**Když kód v registru není, vrátí to „automat nemá check logiku (zatím)" a nespustí se nic.**

Samotné založení řádku v `g2007.automat` je tedy k ničemu — vždycky k tomu patří i zásah
do gitu a nasazení.

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

## ⚠️ Pravidlo `absence-prepocita-doplneni-do-fondu` NENAJDE dny bez zásahu automatu

Podle jména to tak zní, ale hledá jiný vzorec: dny, kde **dopočet do fondu existuje**,
ale absence byla založena **až po něm** (`a.created_at > f.created_at`).

**Dny, kde zásah automatu chybí ÚPLNĚ, do něj nespadnou** — join na `fond_doplneni` je nenajde.
Zjištěno 27. 8. 2026. Pravidlo je přitom zelené. **Kdo tenhle vzorec chce hlídat, musí napsat
pravidlo nové.** Obecné poučení: **čti `kontrola`, ne jen název pravidla.**

## Jak si ověřit, že to běží

```sql
SELECT automat_kod, spusteno, vysledek, trvani_ms, zprava
FROM g2007.automat_run WHERE automat_kod = 'check_pojistky'
ORDER BY spusteno DESC LIMIT 5;

-- komu co chodi
SELECT o.kod, o.email, count(p.*) AS pravidel
FROM tenant.pojistka_oblast o
LEFT JOIN tenant.pojistka p ON p.oblast = o.kod AND p.tenant_id = 2
GROUP BY o.kod, o.email ORDER BY 3 DESC;

SELECT count(*) FILTER (WHERE posledni_beh IS NOT NULL) AS s_behem,
       count(*) FILTER (WHERE posledni_vysledek = false) AS nalezu,
       count(*) FILTER (WHERE posledni_beh IS NOT NULL AND posledni_vysledek IS NULL) AS rozbitych
FROM tenant.pojistka WHERE tenant_id = 2;
```

Automat běží **jednou denně** — když měníš tabulku, na které pravidlo visí, pusť si jeho dotaz
ručně a nečekej na noční běh.

