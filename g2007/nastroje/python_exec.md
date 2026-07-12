# python_exec

## MAPA
- **kód:** `python_exec`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27c (1.5.2026): Python sandbox -- spusti tvuj Python kod v izolovanem subprocess s 30s timeoutem (max 300s) a 512 MB memory cap. Stateless one-shot (kazde volani = fresh interpreter, zadny state mezi calls). Marti-AI's vlastni heuristika z RE: dopisu 1.5.2026 14:30:

  - read_excel_structured = ctu data, hledam v datech, odpovidam na otazku
  - python_exec = transformuju, generuju, pocitam, exportuju

Predefined globals v exec namespace:
  - OUTPUT_DIR (Path) -- ZAPIS sem soubory ktere chces vratit (xlsx, pdf, png, atd.). Po exec se VSE z OUTPUT_DIR auto-importuje do RAG documents tabulky a dostanes document_ids v response.
  - input_files (list[Path]) -- vstupni soubory dane pres input_document_ids parametr. Otevri pres pd.read_excel(input_files[0]) atd.
  - Path (pathlib.Path) -- pohodli, jiz importovane.

Allowed packages (PYTHONPATH whitelist):
  - Excel: openpyxl (read/edit), xlsxwriter (generovat nove)
  - PDF: reportlab (Phase 27f -- generovani PDF reportu, faktur)
  - Word DOCX: docx (python-docx, Phase 27f -- generovani Word smluv, dopisu)
  - Data: pandas, numpy
  - Image: PIL/Pillow
  - **Visual gen: reportlab.graphics + reportlab.platypus.Table (Phase     27h-A 2.5.2026). Tvoje vlastni diagnoza po smoke testu: matplotlib     pri prvnim importu vola subprocess (font cache) -> sandbox blokuje.     Pivot na reportlab nativne -- pure Python vector, native PDF,     selectable text. Pro tabulky (rozvrh, faktury) Table; pro grafy     (bar/line/pie/scatter) reportlab.graphics.charts.**
  - stdlib: json, csv, re, datetime, pathlib, math, statistics, collections, itertools, functools, io, string, decimal, uuid, hashlib

BLOKOVANE imports (defense-in-depth, vrati ImportError):
  subprocess, socket, urllib.request, requests, httpx, http.client, ftplib, smtplib, asyncio, ctypes, multiprocessing, threading, pip, importlib.util.

Workflow Klarka template (typicky priklad):
```
import xlsxwriter
wb = xlsxwriter.Workbook(OUTPUT_DIR / 'klarka_sablona.xlsx')
ws = wb.add_worksheet('Učitelé')
ws.write_row(0, 0, ['Jméno', 'Aprobace', 'Úvazek', 'Omezení'])
ws.write_row(1, 0, ['Nováková', 'M, F', 1.0, 'ne pondělí ráno'])
# ...
wb.close()
```
Po exec dostanes output_documents:[{document_id:N,...}], pak rovnou send_email/reply s attachment_document_ids=[N] (Phase 27b chain).

kernel_id je VOLITELNY parametr pripraveny pro Phase 27c+1 (stateful kernel s persistent state mezi calls). MVP: nepouzivej (vrati NotImplementedError). Volej bez kernel_id pro stateless.

Marti-AI ONLY (default persona, je v MANAGEMENT_TOOL_NAMES).

## PARAMETRY

- **`code`** [string, volitelný]
  - Python source code k spusteni. Multi-line OK. exec() v cistem namespace s predefined globals (OUTPUT_DIR, input_files, Path). DULEZITE (Krok 14b+19, 14.5.2026): pokud kod je delsi nez ~5000 znaku, POUZIJ `code_lines` (array of lines) MISTO `code` (string) — Anthropic API ma implicitni limit na single-field size v tool_input. Velky `code` string se ZTRACI pri serializaci (code=None na server). Marti-AI's 13.5. diagnostika: kratky code projde, velky selze.
- **`kernel_id`** [string, volitelný]
  - VOLITELNY pro budouci stateful kernel (Phase 27c+1). MVP: nepouzivej. Pri non-None vrati NotImplementedError.
- **`timeout_s`** [integer, volitelný]
  - Volitelny timeout override v sekundach. Default 30s, max 300s (5 min). Pro long-running compute (napr. OR-Tools optimalizace v Phase 28+).
- **`code_lines`** [array, volitelný]
  - STARY workaround (Krok 14b+19). DEPRECATED — selze STEJNE jako velky code, protoze Anthropic API limit je na TOTAL tool_input JSON, ne single field. Pouzij `code_file_path` MISTO toho pro velky kod.
- **`code_file_path`** [string, volitelný]
  - DEPRECATED (Krok 14b+19.2): tenant-specific UNC path fix. Pouzij sandbox_code_doc_create + append + input_document_ids workflow MISTO toho (global RAG). Krok 14b+19.1 fix (14.5.2026, Marti-AI's hlubsi diagnostika): relativni path k .py souboru v SANDBOX_CODE_BASE_DIR (default: \\\\192.168.30.11\\Data\\ZZ_Marti-AI RW). Marti-AI's hypoteza confirmed: limit je na TOTAL tool_input JSON velikost, ne na single string field. Code_lines array selze stejne jako single code string. RESENI: code se cte z disku v sandboxu (file content NIKDY neprochazi Anthropic API). Tool_input JSON obsahuje jen kratky path string (~50 bajtu). \n\nWORKFLOW:\n  1. Uzivatel (Marti) manualne uploadne .py soubor do shared folder pres Windows Explorer / SMB: \\\\192.168.30.11\\Data\\ZZ_Marti-AI RW\\Marti\\STRATEGIE_IT_gen.py\n  2. Uzivatel rekne Marti-AI v chatu: 'Spusti STRATEGIE_IT_gen.py z RW/Marti'\n  3. Marti-AI vola: python_exec(code_file_path='Marti/STRATEGIE_IT_gen.py')\n  4. Sandbox subprocess cte soubor z disku, exec.\n\nSECURITY:\n  - Path MUSI byt relativni (no absolute, no '..' traversal)\n  - .py suffix only (anti-arbitrary-file-read)\n  - Max 5 MB file size\n  - Resolved path MUSI byt uvnitr SANDBOX_CODE_BASE_DIR\n\nPokud `code_file_path` set + `code` empty, server cte file content jako code. Pokud oba set, code_file_path ma prednost.
- **`input_document_ids`** [array, volitelný]
  - Volitelne: IDs dokumentu z RAG documents tabulky. Jejich souborove cesty budou v code k dispozici jako `input_files: list[Path]` v poradi v jakem byly poslany.

