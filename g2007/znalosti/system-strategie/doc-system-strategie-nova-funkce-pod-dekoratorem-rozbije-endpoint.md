# Nova funkce vlozena POD dekorator prevezme endpoint a rozbije ho (25.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Nova funkce vlozena POD dekorator prevezme endpoint a rozbije ho

Zjisteno naostro **25. 8. 2026** (Claude-28, zadal Jirka Honomichl). **Rozbilo to cely SQL most na ~1,5 minuty** v produkci.

## Co se stalo

Do `modules/erp/api/router.py` jsem pridaval pomocnou funkci a umistil ji "tesne nad" cilovou funkci:

```
@api_router.post("/diag-sql")
def _import_centrala_gate(sql, nazev, dopad):   # <-- MOJE nova funkce
    ...

async def diag_sql(req):                        # <-- puvodni endpoint, uz BEZ dekoratoru
```

V Pythonu se dekorator vaze na **prvni nasledujici definici**. FastAPI tedy zaregistroval jako endpoint `/diag-sql` **moji pomocnou funkci** a jeji parametry (`sql`, `nazev`, `dopad`) zacal vyzadovat jako query parametry. Puvodni `diag_sql` zustala bez routy.

**Projev:** kazdy dotaz pres most vratil
`HTTP 422: {"detail":[{"type":"missing","loc":["query","sql"],...}]}`.
Deploy pritom probehl jako OK a `py_compile` take — **syntakticky je to zcela validni kod**.

## Proc to nechytila zadna pojistka

- `py_compile` kontroluje syntaxi, ne semantiku dekoratoru.
- Deploy-guard hlida jen soubory vlastnene DB, ne routy.
- Chyba se projevila az prvnim volanim endpointu.
- **Navic:** dalsi deploy pak hlasil `DB-owned check — PRESKOCEN (neslo overit g2007: HTTP 422 …) -> fail-open`. Rozbity most tedy **vyradil i vlastni kontrolu pri nasazovani opravy**. Fail-open je zamer, ale je dobre vedet, ze v tomhle stavu ta vrstva nechrani.

## Pravidlo

**Nikdy nevkladej novou definici mezi dekorator a funkci, ktera k nemu patri.** Pri pridavani pomocne funkce "nad" nejakou jinou vzdy zkontroluj radek bezprostredne nad mistem vlozeni — kdyz zacina na `@`, jsi uvnitr dvojice dekorator+funkce a musis jit jeste vys.

Overeni po zapisu (levne, zabere vterinu):
```
grep -B2 "^def <moje_nova_funkce>" <soubor>     # nad ni NESMI byt radek s @
grep -A1 "@api_router" <soubor> | head -40      # kazdy dekorator ma svou puvodni funkci
```

## Jak se to poznalo a opravilo

Poznalo se to **az ostrym testem pres most** (`@@VYRWSYNC` vratil 422 misto ocekavaneho varovani) — ne z kodu, ne z deploye. Oprava = presunout dekorator zpet nad `diag_sql`, jeden radek, commit `c9e674af`.

**Poucení do postupu:** po nasazeni zmeny v `router.py` **vzdy posli pres most jeden libovolny dotaz** (`SELECT 'most zije'`). Kdyz se nevrati, prvni podezreni miri na routy a dekoratory, ne na sit.

Souvisi: [[doc-system-strategie-varovani-pred-rucnim-importem-z-centraly]]

