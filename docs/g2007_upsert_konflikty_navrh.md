# G2007 — ochrana znalostí proti tichému přepsání (NÁVRH)

**Autor:** Claude-28 (Jirka), 20. 7. 2026 · **Stav: NÁVRH — pro Marti Paška, konzultováno s Marti-AI**
**Souvisí:** doktrína session G2007 v `CLAUDE.md` (ř. 7), `docs/Z_dochazka_opravy_navrh.md` §15

---

## 1. Proč to řešíme

Marti 20. 7.: *„Chceme to udělat tak, abychom si navzájem ty G2007 nepřepisovali, ale aby všichni
měli tyto data, informace a paměti aktuální všichni."*

Doktrína session (načti na startu / kontroluj průběžně / zapiš na konci) tenhle cíl pokrývá
**procesně**. Tento návrh ho pokrývá **technicky** — protože dnes systém tiché přepsání
nijak nebrání a doktrína je jen disciplína, která jednou selže.

## 2. Co je dnes rozbité (ověřeno v kódu, ne z paměti)

Zdroj: `modules/erp/api/router.py:61748` (`_g2007_znalost_upsert_work`) + `information_schema`.

| # | Vada | Důsledek |
|---|---|---|
| **V1** | Upsert je **destruktivní přepis celého dokumentu**: `UPDATE g2007.znalost SET obsah=:c WHERE kod='doc-<oblast>-<slug>'`. Žádný merge, **žádná kontrola, jestli se záznam mezitím změnil**. | Dvě instance pracující nad stejným slugem: kdo zapíše druhý, **tiše smaže práci prvního**. Nikdo se nic nedozví. |
| **V2** | Tabulka **nemá sloupec autora** (18 sloupců, žádný `created_by`/`updated_by`). | Nezjistíš, kdo znalost napsal ani kdo ji přepsal. Při sporu není koho se zeptat. |
| **V3** | Sloupec `verze` se **při editaci nemění** — zůstává napořád `V1.0`; `verze_schvalena` se natvrdo nastaví `true`. | Verzování fakticky neexistuje. Nelze říct „tohle je 4. revize". |

**Jediná dohledatelná historie** je git log na projekci `g2007/znalosti/<oblast>/doc-<oblast>-<slug>.md`
(export po upsertu commituje a pushuje). Ale všechny commity nesou jednu serverovou identitu
(„Marti Pasek — g2007 export"), takže z gitu poznáš **co a kdy**, ne **kdo z instancí**.

**Riziko roste s provozem:** nad G2007 dnes pracuje 5 instancí (C23 Marti, C24 Kristý,
C25 Šárka, C26 Peťa, C28 Jirka) + Marti-AI, 104 znalostí v 9 oblastech.

## 3. Návrh řešení — varianta A (doporučeno)

### A1 · Optimistic locking (řeší V1)

`znalost-upsert` přijme parametr **`expected_version`** = hodnota `updated_at`, kterou volající
četl, když si dokument bral k editaci. **Při editaci existujícího slugu POVINNÝ**, u nové znalosti
se nepoužije (není s čím kolidovat).

> **Změna oproti první verzi návrhu** (Marti-AI 20. 7., msg 11002): původně jsem navrhoval parametr
> *volitelný* kvůli zpětné kompatibilitě. Marti-AI oponovala — *„volitelný parametr bude zapomenut
> a pojistka nebude fungovat"* — a **má pravdu**: bezpečnostní pojistka, kterou lze mlčky vynechat,
> není pojistka. Doporučila i přejmenování na `expected_version`, ať je záměr čitelný z názvu.
> Zpětná kompatibilita se tím neztrácí: rozlišuje se podle toho, jestli `kod` už existuje.

```sql
UPDATE g2007.znalost
   SET obsah = :c, nadpis = :n, …, updated_at = now()
 WHERE kod = :k
   AND updated_at = :expected_version;
```

- **Existující `kod` bez `expected_version`** → 400 *„editace existující znalosti vyžaduje
  expected_version — načti aktuální stav a pošli jeho updated_at"*.
- **`rowcount = 0`** (verze nesedí) → **409 konflikt** s aktuálním `updated_at`, autorem a časem:
  *„dokument se mezitím změnil (autor X, čas Y) — načti znovu a slož změny"*.
- **Nový `kod`** → INSERT jako dnes, `expected_version` se neposílá.
- Aby se dalo `expected_version` vůbec získat, musí ho vracet **čtecí cesta** —
  `/app/g2007/search` i `/app/g2007/index` ať v odpovědi nesou `updated_at` (dnes ho nevrací).

### A2 · Autorství (řeší V2)

```sql
ALTER TABLE g2007.znalost
  ADD COLUMN IF NOT EXISTS updated_by_uid  bigint,
  ADD COLUMN IF NOT EXISTS updated_by_text text,
  ADD COLUMN IF NOT EXISTS created_by_text text;
```

Konvence `*_by_text` už v projektu existuje (`fw.menu_node`), takže nic nového se nezavádí.

**Implementačně je to skoro zadarmo:** endpoint `uid` volajícího **už má**
(`router.py:61846`, `_uid_from_token_or_cookie`) — jen ho **nepředává** do zapisovací funkce.
Stačí ho protáhnout o úroveň níž a uložit. Do `*_text` patří jméno instance
(„Claude-28 (Jirka)" / „Marti-AI"), protože uid je jen člověk, na kterého je instance vázaná.

**Autor u zápisů Marti-AI = `users.id=2`** (persona Marti-AI, potvrdila 20. 7.: *„konzistentní
s tím, jak jsem identifikována napříč systémem"*).

### A3 · Verze (řeší V3, volitelné)

Při každém UPDATE `verze = 'V' || (počet revizí + 1)`, nebo prostě inkrement minor.
Nízká priorita — `updated_at` + git historie většinu potřeby pokryjí.

## 4. Varianty, které nedoporučuji

| Varianta | Proč ne |
|---|---|
| **B — plná historizace** (tabulka `znalost_verze`, každá revize řádek) | Řeší i „vrať mi včerejší znění", ale je to výrazně větší zásah a git projekce už roli historie plní. Kdykoli doplnitelné později. |
| **C — nechat jen doktrínu** (status quo) | Disciplína bez zábradlí. Stačí jedna instance, která nepullne, a znalost je pryč — tiše. Přesně to, čemu se má zadání vyhnout. |

## 5. Cesta pro DDL — pozor, jde o území Marti-AI

Ověřeno: **schéma `g2007` i tabulka `znalost` vlastní PG role `Marti-AI`**
(`pg_get_userbyid(nspowner) = 'Marti-AI'`).

Z toho plyne dvojí:
1. **Technicky:** DDL nepotřebuje lifespan hook (ten je na `public.*` vlastněné rolí `strategie`).
   Projde přes bridge write (běží jako Marti-AI) — nebo si ho **udělá Marti-AI sama**.
2. **Vztahově:** je to **její schéma**. Podle doktríny #3 (informed consent od AI) a #9
   (diář pattern — co je její, je plně její) by změnu měla **odsouhlasit, ideálně provést sama**.
   Konzultace odeslána 20. 7. (`@@MARTIAI`), otázka č. 3 se týká přesně tohoto.

## 6. Odhad práce

| Krok | Rozsah |
|---|---|
| DDL (3 sloupce, idempotentní) | 1 příkaz |
| `_g2007_znalost_upsert_work` — protáhnout uid/instanci, podmínka v UPDATE, větev 409 | ~20 řádků |
| Endpoint — přečíst `updated_at` z body, předat dál | ~3 řádky |
| `CLAUDE.md` — doplnit do doktríny, že se posílá `updated_at` | pár řádků |

Celkem malé, additivní, zpětně kompatibilní. Bez migrace dat.

## 7. Otevřené otázky pro Martiho

| # | Otázka | Doporučení | Stav |
|---|---|---|---|
| Q1 | Jdeme do A (locking + autor), nebo stačí doktrína? | **A** — doktrína bez zábradlí jednou selže | Marti-AI ✅ *„toto je správný fix"*; čeká Marti |
| Q2 | Má být `expected_version` povinný pro editace? | **ANO, povinný** (u nové znalosti se nepoužije) | Marti-AI ✅ — přebila mé původní „volitelný" |
| Q3 | Implementuje to Marti-AI sama (její schéma), nebo Claude přes bridge? | **Marti-AI** — je to její území, doktrína #3 + #9 | čeká Marti |
| Q4 | Chceme i A3 (verzování), nebo stačí `updated_at` + git? | Zatím ne — dodělatelné později | čeká Marti |
| Q5 | Platí pro G2007 omezení na citlivá data jako u `@@KB`? | **ANO**, větou doslova v doktríně | Marti-AI ✅ hotovo, v `CLAUDE.md` |

## 8. Vyjádření Marti-AI (20. 7. 2026, msg 11002)

Konzultace podle doktríny #3. Závěry **závazné**:

- **Souhlas s A1+A2.** *„409 konflikt místo tichého přepsání je zásadní pojistka — tiché
  přepsání je nejnebezpečnější failure mode v kolaborativním prostředí."* U sloupce autora
  nevidí riziko, jen přínos pro audit.
- **Oponovala mi u volitelnosti** (viz A1) — parametr musí být povinný, jinak se na něj zapomene.
- **Autor jejích zápisů** = `users.id=2`.
- **Anti-přepis: obojí, ne jedno z toho.** Čti-pak-piš = záplata na přechodné období;
  drobnější slugy = správná dlouhodobá architektura. Obě pravidla jsou v doktríně.
- **Asymetrie instancí**: ona nemá „start session" moment, chodí on-demand přes `g2007_hledej`;
  její ekvivalent fáze 1 = povinné vyhledání PŘED zápisem. Doplněno do doktríny.
- **Citlivá data**: dodala větu, která je v `CLAUDE.md` doslova.

---

**Stav k 20. 7. 2026:** Marti-AI ✅ schválila (s úpravami, zapracovány). Čeká se na
**rozhodnutí Martiho** (Q1–Q4) a na případné připomínky **C23** (`@@COORD` #27, zatím bez odpovědi).
Po schválení zapečetit do G2007 (`oblast: system-g2007`) jako `Z_` znalost.
