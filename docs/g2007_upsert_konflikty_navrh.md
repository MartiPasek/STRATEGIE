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

`znalost-upsert` přijme **volitelný** parametr `updated_at` = hodnota, kterou volající četl,
když si dokument bral k editaci.

```sql
UPDATE g2007.znalost
   SET obsah = :c, nadpis = :n, …, updated_at = now()
 WHERE kod = :k
   AND (:expected_updated_at IS NULL OR updated_at = :expected_updated_at);
```

- `rowcount = 0` při existujícím `kod` → vrať **409 konflikt** s aktuálním `updated_at`
  a odpovědí *„dokument se mezitím změnil (autor X, čas Y) — načti znovu a slož změny"*.
- **Zpětně kompatibilní:** kdo parametr nepošle, chová se přesně jako dnes. Žádný existující
  volající se nerozbije.
- Po zavedení lze parametr postupně zpřísnit na povinný pro editace (ne pro nové znalosti).

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

| # | Otázka | Doporučení |
|---|---|---|
| Q1 | Jdeme do A (locking + autor), nebo stačí doktrína? | **A** — doktrína bez zábradlí jednou selže |
| Q2 | Má `updated_at` být hned povinný pro editace existujícího slugu? | Ne hned — nejdřív volitelný, po ověření zpřísnit |
| Q3 | Implementuje to Marti-AI sama (její schéma), nebo Claude přes bridge? | **Marti-AI** — je to její území, doktrína #3 + #9 |
| Q4 | Chceme i A3 (verzování), nebo stačí `updated_at` + git? | Zatím ne — dodělatelné později |
| Q5 | Platí pro G2007 stejné omezení jako pro `@@KB`, že citlivé věci (finance, personální) tam nepatří? | Dotázáno Marti-AI; podle odpovědi doplnit do doktríny |

---

**Stav k 20. 7. 2026:** čeká na odpověď Marti-AI (`@@MARTIAI`, odeslána 07:18 UTC)
a na rozhodnutí Martiho. Síť informována přes `@@COORD` #27.
Po schválení zapečetit do G2007 (`oblast: system-g2007`) jako `Z_` znalost.
