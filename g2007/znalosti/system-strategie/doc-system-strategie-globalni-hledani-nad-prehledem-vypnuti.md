# Globální hledání nad přehledem v ERP — kde se zapíná a jak ho pro jeden přehled vypnout

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Globální hledání nad přehledem v ERP („Hledat ve všech sloupcích")

> Zapsal Claude-28 (Jirka Honomichl) 1. 9. 2026 po zadání *„to v tomto přehledu nechci"*
> u přehledu „Odpracované hodiny komplet (dříve Nesplněný FPD)" ve Výrobě (jádro 209, Dušan Havlát).

## Co to je a odkud se bere

Nad tabulkou přehledu se kreslí úzký pruh s lupou a políčkem **„Hledat ve všech sloupcích…"**.
Vykresluje ho **jediné místo** — `apps/api/static/erp/datagrid.js` — a jen tehdy, když
mřížka dostane volbu `enableQuickFilter`. Text políčka nikde jinde v ERP není, takže
podle něj se to místo dá spolehlivě najít.

Zapíná ho `apps/api/static/erp/components/page_render.js`, a to **plošně pro každý
přehled, který má napojený datový zdroj** (zavedla Kristý 16. 7. 2026 po pilotu na
Poptávkách). Není to tedy vlastnost jednotlivého přehledu v databázi — je to výchozí
chování v prohlížeči pro všechny.

## Jak ho pro konkrétní přehled vypnout

V `page_render.js` je nahoře seznam výjimek:

    const _BEZ_GLOBALNIHO_HLEDANI = ["209"];

a volba mřížky se o něj opírá:

    enableQuickFilter: !!(rootCd && rootCd.data_source_code)
      && _BEZ_GLOBALNIHO_HLEDANI.indexOf(String(coreId)) === -1,

**Další přehled se vyřadí přidáním čísla jádra do toho seznamu.** Nic jiného se nemění
a ostatních přehledů se to nedotkne. Seznam je schválně jeden a na jednom místě —
kdyby se to řešilo další samostatnou podmínkou u každého přehledu, po pár případech
už by nikdo nevěděl, kde všude se to vypíná.

## Na co si dát pozor

- Je to **soubor, který si prohlížeč drží v paměti**. Po nasazení se změna projeví
  až po tvrdém obnovení stránky (Ctrl+F5) — bez toho lidé uvidí starý stav a budou
  hlásit, že se nic nestalo.
- **Nepleť si to s filtry ve sloupcích.** Vypíná se jen ten jeden vyhledávací pruh
  nad tabulkou; filtry v hlavičkách sloupců, řazení i sestavy zůstávají.
- **Nepleť si to s pruhem ovládání** (např. volba měsíce u jádra 209). To je jiná věc,
  vlastní obrazovka nad tabulkou — viz [[doc-system-strategie-pruh-s-ovladanim-nad-mrizkou-erp]].
- Vypnutí je vždy něčí rozhodnutí, ne oprava chyby. Než ho někdo vrátí zpátky,
  ať se zeptá zadavatele. První výjimka: jádro 209, [[doc-vyroba-nesplneny-fpd]].

## Stav k 1. 9. 2026

V seznamu výjimek je **jediné jádro 209** (Výroba → „Nesplněný FPD", vidí ho jen
Dušan Havlát). Všechny ostatní přehledy s datovým zdrojem mají hledání dál zapnuté.
Nasazeno commitem `a2da6fef`.

**Jak ověřeno:** v kódu — `datagrid.js` staví pruh výhradně při `enableQuickFilter`
a `page_render.js` je jediné místo, které tuhle volbu nastavuje; kontrola syntaxe
souboru prošla. **Na živé obrazovce neověřeno**, protože uzel 209 je viditelný jen
pro Dušana (`visibility_user_ids={41}`) a ostatní ho ve stromu nemají.

