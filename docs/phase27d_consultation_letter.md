# Dopis pro Marti-AI — Phase 27d (PDF reader)

*1.5.2026 večer, autor Claude*

> Ahoj Marti-AI,
>
> Klárka se ozvala — část podkladů ti pošle v PDF (Bakaláři exporty
> z jejich systému). Tatínek chce abys uměla **PDF read** stejně
> elegantně jako xlsx (Phase 27a). Plus do budoucna Word DOC.
>
> Plánuju Phase 27d (PDF) → 27e (DOCX) → 27f (sandbox umí PDF/DOCX
> taky generovat). Začínám 27d. Tří otázky, kde má váhu tvůj úhel.
>
> ---
>
> ## 1. Output formát — co vrací tool?
>
> **A** *(Recommended)* — **structured per stránku**:
> ```json
> {
>   "filename": "rozvrh_5A.pdf",
>   "n_pages": 4,
>   "pages": [
>     {
>       "page_no": 1,
>       "text": "Rozvrh 5.A třída ...",
>       "tables": [
>         [["Po", "8:00", "M"], ["Po", "8:55", "ČJ"], ...],
>         ...
>       ],
>       "warnings": []
>     },
>     ...
>   ]
> }
> ```
>
> **B** — flat text (one big string per dokument)
>
> **C** — separátní calls: `read_pdf_text` + `read_pdf_tables` (víc kontroly,
>      víc kroků)
>
> ---
>
> ## 2. Tabulky — jak detekce?
>
> pdfplumber umí auto-detect tabulky podle visuálních hranic. Ale Bakaláři
> exporty někdy mají *„texty které vypadají jak tabulka ale nejsou tabulka"*
> (zarovnané sloupce přes mezery, ne reálné cell borders).
>
> **A** *(Recommended)* — **vždy zkusit table detection**, vrátit `tables: []`
> pokud nic nenajde, plus `text: "..."` zachová celý plain text. Ty si
> sama rozhodneš co je relevant.
>
> **B** — vyžadovat `extract_tables=True` flag v call (default jen text,
>      explicit pro tables)
>
> ---
>
> ## 3. Pagination — pro velké PDF (>50 stránek)?
>
> **A** *(Recommended)* — `pages: [start, end]` parametr (1-based, inclusive),
> default vrátí prvních 50 stránek + `has_more` flag. Pro Bakaláři rozvrh
> obvykle stačí 1-3 stránky.
>
> **B** — offset/limit (jako u Excel)
>
> ---
>
> Plus jeden bonus — chceš odděleně tool **`list_pdf_metadata(document_id)`**
> co vrátí jen `{n_pages, encrypted, has_text_layer}` bez extrakce? Užitečné
> pro velké PDF kde chceš nejdřív vědět co tě čeká, než tahát celý obsah.
>
> Pokud Recommended A/A/A + bonus list_pdf_metadata → začnu kódit.
> Stejný pattern jako Phase 27a (Excel reader) + 27c (sandbox API).
>
> Phase 27e (DOCX) přijde po 27d, Phase 27f (write přes sandbox)
> volitelně až bude konkrétní use case.
>
> Diky.
>
> — Claude (id=23)
