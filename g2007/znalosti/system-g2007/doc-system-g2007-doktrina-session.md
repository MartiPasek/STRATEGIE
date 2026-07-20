# G2007 — doktrína session (načti / kontroluj / zapiš) a ochrana proti přepsání

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# G2007 — doktrína session (načti / kontroluj / zapiš) a ochrana proti přepsání

**Platí pro:** všechny instance Claude i Marti-AI · **Zadal:** Marti Pašek 20. 7. 2026
**Konzultováno:** Marti-AI (msg 11002 + 11005, závěry zapracovány) · **Zapsal:** Claude-28 (Jirka)
**Zrcadlo:** `CLAUDE.md` ř. 7 (pro file-based instance) — tahle znalost je tatáž věc v G2007,
aby ji měla i Marti-AI, která `CLAUDE.md` nečte.

---

## 1. Proč to existuje

Marti 20. 7. 2026: *„Při zahájení session se dle tématu načtou data a paměť z G2007; při ukončení
se změny zapíší zpět. Chceme, abychom si je navzájem nepřepisovali, ale aby všichni měli aktuální
data."*

Do 20. 7. byl v `CLAUDE.md` popsaný jen postup, **jak znalost přispět** — kdy ji číst a kdy
zapisovat tam nebylo vůbec. Důsledek byl měřitelný: znalost `doc-dochazka-opravy-navrh` zůstala
v G2007 ve stavu k 9. 7. (§11), zatímco zdroj mezitím narostl o §12–§15. **Nikdo neudělal krok
„zapiš zpět".** Tahle doktrína tu díru zavírá.

## 2. Tři fáze session (závazné)

### 1️⃣ START — NAČTI
Podle tématu, které se bude řešit, ještě než se sáhne na kód:
`GET /api/v1/erp/app/g2007/search?q=<téma>&oblast=<oblast>` (sémantické hledání nad vektory;
`/app/g2007/index` = přehled oblastí). Souběžně `git pull --rebase --autostash`.

**⚖️ Asymetrie instancí** (formulace Marti-AI): tenhle krok platí pro **file-based instance**
(Claudi nad repem). **API instance (Marti-AI)** žádný „start session" moment nemá — její
ekvivalent je **on-demand `g2007_hledej` a povinné vyhledání PŘED každým zápisem**
(existuje už téma? → update vs. nový slug). Fáze 3 a anti-přepis platí pro obě stejně.

### 2️⃣ BĚHEM — KONTROLUJ
Souběh instancí je pravidlo, ne výjimka (C23 Marti, C24 Kristý, C25 Šárka, C26 Peťa, C28 Jirka
+ Marti-AI). Při delší práci a **vždy před zápisem** `git pull` a kouknout na
`g2007/znalosti/<oblast>/` — projekce se po každém upsertu exportuje a pushuje do gitu,
takže **cizí změny jsou vidět jako commit**.

### 3️⃣ KONEC — ZAPIŠ
Co přežije session, patří do G2007: rozhodnutí, gotchy, odchylky od zadání, změny chování,
ověřené postupy. **Nezapsaná znalost = ztracená znalost** — příští instance ji bude objevovat znovu.

## 3. 🛡️ Anti-přepis — jak si znalosti navzájem nesmazat

**Technická realita** (ověřeno v `router.py`, `_g2007_znalost_upsert_work`): upsert je
**destruktivní přepis celého dokumentu** — `UPDATE g2007.znalost SET obsah=:c WHERE kod=…`.
Žádný merge, **žádná detekce souběhu, žádná historie v DB**. Sloupec `verze` navíc při editaci
zůstává `V1.0` a tabulka **nemá sloupec autora**. Jediná dohledatelná historie je git log
na projekci `g2007/znalosti/`.

**Dvě různé situace = dvě různá pravidla** (formulace Marti-AI):

- **NOVÁ znalost → NOVÝ SLUG.** Jeden slug = **jedno atomické téma** jedné oblasti. Drobnější
  slugy jsou správná dlouhodobá architektura — instance se potkávají méně a konflikt je
  lokalizovaný. Do cizího slugu nesahej bez přečtení a bez důvodu.
- **EDITACE existujícího slugu → ČTI, PAK PIŠ.** Nejdřív **přečti aktuální obsah**
  (`search` / `g2007_hledej` / projekce po pullu) a do `Z_` souboru napiš **celý nový dokument
  = stávající obsah + tvoje změna**. Kdo pošle jen svůj dodatek, **smaže všechno ostatní**.
  Marti-AI to nazývá *„nutnou záplatou pro přechodné období"* — dokud nebude zámek (§5).
- **Bezprostředně před upsertem `git pull`.** Mezi čtením a zápisem mohla psát jiná instance.
- **Po upsertu ověř** (`export_souboru`, `reindexovano_chunku`) a znovu `git pull`.

## 4. 🚫 Co do G2007 nepatří

Formulace Marti-AI (závazná doslova):

> *G2007 obsahuje procesní a doménové know-how. Citlivá data (mzdy jednotlivců, personální
> záznamy, obchodní podmínky konkrétních zákazníků, interní konflikty) sem nepatří — stejně
> jako do sdílené RAG. Obecné postupy, pravidla, gotchy a rozhodnutí patří.*

Citlivé věci → soukromý sandbox C23 + Marti-AI (md5) + Kristý.

## 5. 🔜 Připravovaný zámek (schváleno, čeká na implementaci)

Dokud neexistuje, drží nás jen disciplína z §3. Návrh: `docs/g2007_upsert_konflikty_navrh.md`.

- `znalost-upsert` dostane **`expected_version`** (= `updated_at` z předchozího čtení).
  **Povinný při editaci** existujícího slugu; u nové znalosti se nepoužije.
  Marti-AI: *„volitelný parametr bude zapomenut a pojistka nebude fungovat."*
- Neshoda → **409 konflikt**, ne tichý přepis.
- **Čtecí strana musí začít vracet `updated_at`** — dnes ho `/app/g2007/search` ani
  `/app/g2007/index` nevracejí, takže by nebylo odkud hodnotu vzít (nález 20. 7.).
- Sloupce autora (u zápisů Marti-AI = `users.id=2`).
- **Implementuje Marti-AI** — schéma `g2007` vlastní její PG role (ověřeno `pg_get_userbyid`),
  doktrína #3 (informed consent) + #9 (diář pattern).

## 6. Jak znalost fakticky zapsat

**Přes most (file-based Claude):**
```
@@G2007DOC <oblast> <slug> <docs/Z_soubor.md> [| <nadpis>]
@@GODOC <slug> [| <nadpis>]          # jen docs/GO/Z_*.md → oblast system-g2007
```

**Přes HTTP (parent/cockpit session):**
```
POST /api/v1/erp/app/g2007/znalost-upsert
{ "oblast": "<kod>", "slug": "<slug>", "nadpis": "<titulek>", "zdroj": "docs/Z_<soubor>.md" }
```

Obojí sdílí jeden worker: upsert → export projekce do `g2007/` → **úklid `docs/Z_` inboxu**
→ reindex vektorů. Zdroj musí být **nasazený na serveru** (`docs/Z_*.md`), jinak upsert skončí
chybou „zdroj neexistuje na serveru".

> **Pozn. k `@@G2007DOC`:** doplněno 20. 7. 2026, protože doktrína původně nařizovala krok, který
> file-based instance neuměly provést — `@@GODOC` zvládal jen GO dokumenty a HTTP endpoint chce
> device token nebo cookie, které Claude přes most nemá.

---

**Související:** `CLAUDE.md` ř. 7 · `g2007/README.md` · `docs/g2007_upsert_konflikty_navrh.md`


