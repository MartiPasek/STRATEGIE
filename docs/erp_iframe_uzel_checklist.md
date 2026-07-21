# Checklist: napojení stránky (iframe) na uzel v ERP stromu

> Claude-25, 9.7.2026. Poučení z ladění „Finanční podmínky" — stránka fungovala samostatně,
> ale v ERP rámečku ukazovala rozbitý čtvereček. Příčina: **route stránky neměla hlavičku
> `X-Frame-Options: SAMEORIGIN`** → Caddy default `DENY` zakázal vložení do iframu.
> Tenhle jeden bod nás stál nejvíc času. Drž checklist v tomhle pořadí.

## Když se přehled/stránka v uzlu nezobrazuje (rozbitý čtvereček) — projdi po pořadí:

1. **Binding uzlu** — `fw.menu_node` → `core_id` → `fw.core.code` sedí? Jádro „drafted" (0 comp_defs)?
   A má `page_render.js` hook pro ten `code` (iframe mount)? → SQL:
   `SELECT n.id,n.label,c.code,(SELECT count(*) FROM fw.comp_def WHERE core_id=c.id) FROM fw.menu_node n JOIN fw.core c ON c.id=n.core_id WHERE n.label ILIKE '%…%';`

2. **⚠ HLAVIČKA IFRAME (nejčastější příčina!)** — route té stránky v `apps/api/main.py` (nebo router.py)
   MUSÍ vracet: `"X-Frame-Options": "SAMEORIGIN", "Content-Security-Policy": "frame-ancestors 'self'"`.
   Caddy default = `X-Frame-Options: DENY` → bez override se iframe NEzobrazí (ale samostatně URL jede).
   Vzor: route `/finance` to má; `/finance-podminky` a `/karta-zamestnance` to 8.7. NEměly → oprava 9.7.

3. **Test dvěma pohledy** — nejdřív otevři URL stránky **samostatně** v nové záložce
   (`strategie-ai.com/<cesta>`): jede + data? Když ANO a v ERP rámečku NE → je to bod 2 (hlavička).
   Když NE ani samostatně → chyba stránky/dat, řeš tam.

4. **Po deployi klient** — Ctrl+Shift+R (tvrdé načtení) + přepnout na **AKTUÁLNÍ** verzi
   (patička „běží A/B", blue-green). PWA: zavřít a otevřít appku. Zaseklý service worker:
   F12 → Application → Service Workers → Unregister → Clear site data.

## Rychlé pravidlo
**Nová iframe stránka do ERP uzlu = hned přidej `SAMEORIGIN` hlavičku k její route.** Ušetří to celé ladění.
