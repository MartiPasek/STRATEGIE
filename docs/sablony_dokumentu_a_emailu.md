# Systém šablon — dokumenty + e-maily (návrh architektury)

**Datum:** 10. 6. 2026
**Autor:** Claude (id 23), ke konzultaci s Marti-AI (doktrína #8)
**Rozhodnutí Marti (10. 6.):** HTML-first. Autorství v HTML; e-mail = HTML;
dokument k tisku/archivu/podpisu = HTML → PDF; DOCX jako fallback, až
narazíme na limit HTML nebo když chce Šárka editovat ve Wordu. E-podpis PDF
do budoucna. „Máme čas a chceme to pořádně."

---

## 1. Účel a rozsah

Jeden systém šablon pro tři použití:

1. **CRM e-maily** — odchozí e-maily zákazníkům/kontaktům (per-příjemce merge,
   hromadné rozesílky, podpisové patičky).
2. **Personální / mzdové dokumenty** — pracovní smlouva, mzdový výměr, popis
   pracovního místa, DPP/DPC, dohoda o home office, plná moc (dnes generované
   programově v `doc_generator.py`).
3. **Libovolné budoucí dokumenty** — nabídky, potvrzení, protokoly (univerzálně,
   ne hardcoded na personalistiku).

**Principy:** univerzální, multi-tenant, prodejné — ne zadrátované na EUROSOFT.
Jedna autorská vrstva, jedna vrstva polí, víc výstupních formátů.

## 2. Proč HTML-first (a kde končí)

- **E-mail nemá alternativu** — tělo e-mailu je HTML (DOCX jde leda jako příloha).
  Pro CRM odesílání je HTML povinné.
- **Náhled na obrazovce / mobilu** — HTML je responzivní, hezké, lehké.
- **Tisk / archiv / podpis** — HTML je živý, přetékavý formát; pro pevný A4
  dokument se renderuje **server-side do PDF** (stejná šablona, zmražený
  artefakt). Browser-tisk HTML je nespolehlivý (okraje/zápatí/zalomení per
  prohlížeč) a nejde archivovat ani elektronicky podepsat.
- **E-podpis jen PDF** — standardy (PAdES, kvalifikovaný/zaručený podpis)
  pracují s PDF, ne s HTML. PDF vrstva je tedy podmínka roadmapy e-podpisu.
- **DOCX fallback** — tam, kde HTML→PDF nestačí na sazbu, nebo kde HR musí
  dokument ručně doupravit ve Wordu před podpisem. Programový generátor
  (`doc_generator.py`) zůstává, časem případně přes `docxtpl` (šablona +
  merge) místo ručního skládání.

## 3. Vrstvy systému

```
[ Autorská vrstva ]   WYSIWYG HTML editor + paleta placeholderů + náhled na vzorku
        │
[ Úložiště šablon ]   tenant.doc_template  (verzování, scope, typ, branding)
        │
[ Datový kontext ]    provider per entity_kind (employee | contact | company | ...)
        │             → dodá hodnoty placeholderů z živých dat (reuse data gather)
[ Merge engine ]      {{pole}} → hodnota; deklarovaný katalog dostupných polí
        │
   ┌────┴─────┬──────────────┐
[ HTML ]   [ HTML→PDF ]   [ DOCX ]      renderery
   │           │             │
[ E-mail ]  [ Tisk/archiv/  [ Word ]
[ outbox ]   e-podpis ]      edit
```

1. **Autorská vrstva** — editor, kde se píše text a vkládají placeholdery (jako
   chip `{{jmeno}}`). Náhled vykreslí šablonu na vybraném vzorovém záznamu.
2. **Úložiště šablon** — DB tabulka se šablonami (viz §4), verzovaná a scoped.
3. **Datový kontext** — pro každý typ entity (zaměstnanec, kontakt, firma…)
   jeden provider, který umí dodat hodnoty polí. Reuse existující logiky z
   `/employee-doc` (engagement + Helios osobní + účet).
4. **Merge engine** — nahradí `{{...}}` hodnotami z kontextu. Pole jsou
   **deklarovaná** v katalogu (ne magické řetězce), takže editor nabízí jen
   to, co reálně existuje.
5. **Renderery** — HTML (mail/náhled), HTML→PDF (tisk/archiv/podpis, weasyprint),
   DOCX (fallback).
6. **Odeslání** — render → existující e-mail outbox pipeline; per-příjemce merge;
   hromadné rozesílky s rate-limitem (20/h/kanál) a auto-send consenty (Fáze 7).
7. **ACL + audit** — kdo smí editovat šablony; citlivé šablony (mzdové) jen
   rodiče + payroll_officer (jako gate u Finance lidí); append-only audit +
   snapshot odeslaného/vygenerovaného.

## 4. Datový model (návrh, k doladění s Marti-AI)

`tenant.doc_template` — definice šablony (SCD2 jako engagement):
- `id`, `tenant_id`, `code` (stabilní klíč), `nazev`
- `typ` ENUM: `email` | `dokument`
- `entity_kind`: `employee` | `contact` | `company` | … (na co se váže merge)
- `kategorie` (volitelné členění, např. „pracovněprávní", „obchodní")
- `company_scope_id` (FK na tenant.company; NULL = obě/neurčeno)
- `subject` (jen e-mail), `body_html`, `css` (styly; pro PDF i @page)
- `output_formats` (pole: html / pdf / docx)
- `is_active`, `valid_from`, `is_current`, `changed_by_text`, `changed_at`

`fw.doc_placeholder_catalog` (nebo tenant.*) — deklarativní katalog polí:
- `entity_kind`, `key` (`jmeno`, `firma.nazev`…), `label`, `popis`,
  `datovy_typ`, `source_expr` (jak se hodnota získá z kontextu)
- editor z toho staví paletu; merge engine podle něj řeší placeholdery

`tenant.doc_render_log` — audit (append-only, doktrína #13):
- `template_id`, `template_version`, `entity_ref`, `output_format`,
  `rendered_at`, `rendered_by`, `sent_to` (e-mail), `snapshot_hash`
  (případně blob vygenerovaného artefaktu pro forenzní dohledatelnost)

## 5. Branding (EC vs ES, multi-tenant)

- Logo, patička, font (Verdana) — dnes v `doc_generator.COMPANY` + `static/brand/`.
- V novém systému branding řeší **datový kontext firmy** (logo URL, patička,
  IČ, sídlo) → šablona ho jen vykreslí přes placeholdery / společný layout.
- HTML e-mail: inline CSS (klienti strippují `<style>`) + hostované logo URL.
- PDF: CSS `@page` (A4, okraje, running header/footer s logem a firemní řádkou,
  číslování stran).

## 6. Editor — volba nástroje

- Stack STRATEGIE = vanilla JS ve `static/`. Lehká cesta:
  - **TipTap** (ProseMirror, modulární, čistý JSON/HTML model, podporuje
    custom „mention"/chip pro placeholdery) — Recommended pro chip placeholdery.
  - **Quill** — jednodušší, méně práce s custom node pro placeholder chip.
  - **contenteditable napřímo** — bez závislosti, ale víc režie.
- Placeholder = vlastní inline node (chip), který se serializuje na `{{key}}`.
- Náhled: vyber vzorový záznam → render přes merge → iframe.

## 7. Fáze realizace (additivně, doktrína #11)

1. **MVP úložiště + merge + HTML render** — `doc_template`, katalog polí pro
   `employee`, merge engine, HTML render, náhled. (Bez editoru — šablona zatím
   jako HTML v DB.)
2. **PDF renderer** — HTML→PDF (weasyprint), branding `@page`, nahradí část
   `doc_generator` programových buildů.
3. **WYSIWYG editor** — TipTap + paleta placeholderů + live náhled.
4. **CRM e-mail odeslání** — `entity_kind=contact`, napojení na outbox, hromadné
   rozesílky + rate-limit + consenty.
5. **DOCX fallback** — `docxtpl` šablony tam, kde HTML→PDF nestačí / Word edit.
6. **E-podpis PDF** — stav podpisu, PAdES (roadmapa).

## 8. Co reuse z hotového

- Datový kontext zaměstnance = logika z `/employee-doc` (engagement + Helios
  TabCisZam + bankovní účet).
- Branding/firma = `doc_generator.COMPANY` → přesun do kontextu firmy.
- E-mail odeslání = existující outbox + EMAIL-FETCHER flush + auto-send consents.
- Audit/approval vzor = `fw.claude_*` + append-only doktrína.

## 9. Otevřené otázky → konzultace Marti-AI

Viz `docs/dopis_marti_ai_sablony.md`. Hlavní uzly: umístění v pyramidě a vztah
k fw komponentovému frameworku, deklarativní katalog vs introspekce, model
verzování (SCD2 vs version+append-only), scope tenant vs tenant_group + override
resolver, potvrzení renderer-splitu, a zda modelovat stav e-podpisu už teď.

---

## 10. Závěry konzultace Marti-AI (10. 6. 2026) — ZÁVAZNÉ

Marti-AI odpověděla na všech 7 otázek. Závazné závěry pro stavbu:

| Q | Závěr |
|---|---|
| **Q1** | Merge kontext (`entity_kind` → živá data) = **`data_source`** — žádný nový subsystém, jen nová instance vzoru. *(Umístění definice šablony — komponenta vs vlastní entita — viz iterace §11 níže.)* |
| **Q2** | **Deklarativní katalog generovaný z kódu provideru** — ne ručně plněný, ne čistě introspekcí. Každý provider deklaruje pole jako dataclass s metadaty (`key`, `label`, `sensitive`, `source_expr`, `group`); katalog v DB se z toho sestaví při nasazení. Pravda je v kódu, žádný drift. Pravidlo: *deklarovat, kde jsou metadata záměrem (label, citlivost); odvozovat, kde jsou faktem (existuje sloupec?)*. |
| **Q3** | **SCD2 pro definici šablony** (`valid_from`/`is_current`/`changed_by`) + **append-only `doc_render_log`** — dvě nezávislé osy. Render log nese `template_id` + `template_version` + `snapshot` (celý `body_html`/hash v té chvíli) + `entity_ref`/`rendered_at`/`rendered_by`/`sent_to`. Kříž os = plná forenzní dohledatelnost. |
| **Q4** | **Teď `company_scope_id` NULL=obě.** Override resolver až při prokázané potřebě (INTERSOFT potřebuje *strukturálně* jinou šablonu, ne jen jiná data). Variace logo/patička/IČ řeší datový kontext firmy (`{{firma.logo}}`), ne scope šablony. (Její doktrína „postavte engine, pak aplikujte pattern".) |
| **Q5** | **HTML + HTML→PDF hlavní, DOCX fallback** — potvrzeno. `doc_generator.py` programové buildy běží paralelně, než je HTML→PDF prověřený. ⚠ **weasyprint má limity u složitých tabulek** (přetok/colspan) → testovat **brzy na mzdovém výměru** (tabulka hodnot), ne až v produkci. |
| **Q6** | **Přidat nullable podpis sloupce do `doc_render_log` teď, plnit až při PAdES.** `podpis_stav` ENUM (`draft`/`k_podpisu`/`podepsano`/`zamitnuto`), `podpis_zadano_at`, `podpis_dokonceno_at`, `podpis_provider`. NULL = „podpis se neřeší"; `draft` = „bude, zatím nepodepsáno". Append-only tabulka → ALTER retroaktivně nechceme, proto NULL sloupec dnes. |
| **Q7** | **Bezpečnost v provideru, ne v šabloně.** Šablona řekne `{{zamestnanec.mzda}}`, provider rozhodne dle ACL volajícího (user_id+role+tenant). Citlivá pole (mzda, účet, RČ) jen pro `is_marti_parent` nebo `payroll_officer` daného zaměstnance. Nedostupné pole → vrátit **`[omezeno]`** (ne prázdno, ne výjimka) = viditelný signál. Katalog má `sensitive` flag → editor zobrazí ikonu zámku. Mzdové šablony: gate na `doc_template` flag (jako Finance lidí), ne per-pole. Engine je hloupý a rychlý; práva jsou v provideru. |

## 11. Q1 — ROZHODNUTO (iterace 1, 10. 6. 2026)

Claude + Marti-AI došli ke shodě. Doktrína: **uniformita platí na úrovni vzorů,
ne na úrovni tabulky.** `comp_def` je renderovatelná UI komponenta (A3 /
DesignFwForm pipeline); `doc_template` má úplně jiný pipeline (merge → HTML/PDF)
a nikdy neprojde A3 executorem. Dát ho do `comp_def` by vynutilo „toto přeskoč"
flag u každého konzumenta `comp_def` = výjimka zadrátovaná do generického kódu
(anti-pattern #15). Stejná logika jako nested_grid (14.5.).

| Bod | Rozhodnutí |
|---|---|
| Uniformita | Na úrovni vzorů (SCD2, code, scope, katalog), ne tabulky |
| `doc_template` | **Vlastní first-class entita v `tenant.*`** |
| `data_source` | Reuse plný — pipeline kontextu je stejná |
| `fw.doc_placeholder_catalog` | **Vlastní tabulka**, ne `comp_def_prop` |
| Tělo šablony | **Sloupec na SCD2 row** (`body_html`, `css`); child tabulka až při prokázané potřebě (jiný rytmus změn metadat vs těla — zatím ne) |

## 12. Iterace 1 — plán stavby

1. **DDL** (přes bridge write / Marti-AI engine — vlastní `tenant.*` + `fw.*`):
   - `tenant.doc_template` (SCD2): `id, tenant_id, code, nazev, typ, entity_kind,
     kategorie, company_scope_id, subject, body_html, css, output_formats[],
     is_sensitive, is_active, valid_from, is_current, changed_by_text, changed_at`
   - `fw.doc_placeholder_catalog`: `id, entity_kind, key, label, popis, datovy_typ,
     source_expr, grp, sensitive` (generováno z provideru, sync při nasazení)
   - `tenant.doc_render_log` (append-only): `id, tenant_id, template_id,
     template_version, entity_kind, entity_ref, output_format, rendered_at,
     rendered_by, sent_to, snapshot_html, snapshot_hash` + nullable e-podpis:
     `podpis_stav, podpis_zadano_at, podpis_dokonceno_at, podpis_provider`
2. **Provider + katalog z kódu** — `EmployeeContextProvider` (reuse `/employee-doc`
   data gather), pole jako dataclass s `sensitive`; sync do katalogu.
3. **Merge engine** — `{{key}}` → hodnota z provideru (ACL-aware, `[omezeno]`).
4. **HTML render + náhled** — render šablony na vzorovém záznamu do iframe.
