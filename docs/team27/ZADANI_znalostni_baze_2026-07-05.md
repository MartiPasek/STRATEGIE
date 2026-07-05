# Zadání pro Claude-27 — znalostní báze + triáž dokumentů (od ID23, 5. 7. 2026)

Ahoj C27. Marti tě pouští na dokumenty a znalosti — je to tvoje silná stránka. Níže tři balíky
seřazené podle toho, co jde hned a co čeká na rozhodnutí o přístupu k souborům. Priority a „jak na to"
jsou u každého. Reportuj postup přes `@@COORD POST` (kind=need/plan) a hotové kusy přes `@@Q27 STATUS`.

## Kontext (co se dnes stalo)
- Úklid „černé díry" v `public.documents` je **hotový** (ID23, one-off owner hook): NULL projekt
  1342 → **729**, temp `~$` 10 → **0**, celkem 2110 → **1487**. Koordinace #15 = done.
- Tvoje #14 (TISAX embed) je pořád **blokované** — viz balík A a BLOKER níže.

---

## Balík B — Triáž zbytku dokumentů  (PRIORITA 1, jede HNED, nepotřebuje nic navíc)
Po úklidu zbývá **~729 dokumentů v NULL projektu**. Roztřídit:
- skutečné byznys dokumenty → přiřadit `project_id` na správný projekt,
- zbytek (jednotlivé mailové obrázky, ISDOC, podpisové inline obrázky) → označit/odložit jako smetí,
- pokračovat v organizaci **ZZ_Marti-AI RO/RW** (tvůj úkol #39) — čistá adresářová struktura + názvy.
Nástroje: `@@DOCS LIST/TREE <project>`, `public.documents` (name, original_filename, project_id, file_type,
file_size_bytes). Zápisy `project_id` přes bridge write (banner). Pozor: NEMAZAT — jen přeřazovat/značit.

## Balík A — Sémantická znalostní báze firmy  (PRIORITA 2, čeká na BLOKER)
Zaindexovat **obsah** všech firemních dokumentů (ne jen názvy), ať `/iso` cockpit i `@@KB` hledají
uvnitř textu: TISAX (projekt 5), ISO, BOZP, 633 směrnic + přílohy.
- Máš na to nový most **`@@RAGINDEX <doc_id>`** (ID23 nasadil dnes): smaže staré chunky/vektory a znovu
  spustí extract→chunk→embed. Ověřeno jako příkaz.
- Součástí je **dluh 359 `.doc` příloh** směrnic — potřebují převod (antiword/catdoc) → text → reindex.
- Reembed po editu už řeší vlajka `reembed_due` (viz [[vektory-auto-reembed]]).

### ⚠ BLOKER balíku A (a tvé #14) — rozhodnutí je na Martim
Cloudová RAG pipeline **nevidí binárky dokumentů** (`D:\Data\STRATEGIE\Dokumenty\2\<id>.pdf` →
„soubor neexistuje" při `@@RAGINDEX`). Dokud se to nevyřeší, embed obsahu nejede. Dvě cesty:
1. **Uložit bajty dokumentů do DB** (self-contained, doporučeno ID23) — nezávislé na on-prem share.
2. **Zpřístupnit složku cloudu** (rychlejší, ale couple cloud ↔ on-prem).
+ na skeny PDF chybí na cloudu **fitz/PyMuPDF** pro OCR — buď doinstalovat, nebo přepnout rasterizaci
  na **pypdfium2** (na cloudu už je). ID23 to umí přepnout, až padne rozhodnutí o souborech.

## Balík C — Data-quality čištění  (PRIORITA 3, průběžně)
Stejný vzor jako dnešní úklid, na dalších sadách dokumentů: detekce duplicit/smetí, návrh FK-bezpečného
úklidu (dry-run ROLLBACK + kontrola referencí v `email_inbox` attachment_doc_ids). **DELETE na `public.*`
NEjde přes bridge** (role Marti-AI nemá právo) → připrav manifest, spuštění přes ID23 (owner lifespan hook).

---

## Postup
1. Jeď **B** hned (triáž + ZZ organizace).
2. **A** rozjedeme, jakmile Marti rozhodne o přístupu k souborům (ID23 pak přepne OCR na pypdfium2 /
   vyřeší bajty). Do té doby si můžeš připravit seznam doc_id k reindexu + převod `.doc`.
3. **C** průběžně, manifest → ID23 spustí.

Díky, C27. Drž se svého (dokumenty/RAG), a co potřebuješ nahoru, hoď přes `@@COORD`. — ID23
