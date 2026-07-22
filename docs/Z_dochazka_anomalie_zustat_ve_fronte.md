# Opravy docházky — anomálie ať zůstanou ve frontě jako „hotovo" (návrh)

> Zadala Peťa 22. 7. 2026: *„u nesrovnalostí (automatická kontrola), když si to
> rozkliknu a upravím, tak mi to z hlavního přehledu zmizí a nezůstane mi to tam,
> jako u těch od lidí s tím zeleným Hotovo z fronty."*
> Připravil Claude‑26. **NENASAZENO — návrh k odsouhlasení.**

## Co se děje dnes

Fronta „K vyřešení" má dva druhy položek:

- **Rozpory od lidí** (✋) — po opravě zůstanou, zezelenají „✓ opraveno" a mají
  tlačítko **✓ Hotovo — z fronty**. Zmizí, až je Peťa sama odklikne.
- **Nesrovnalosti z automatické kontroly** — po opravě/stornu **zmizí hned**.
  Peťa ztrácí přehled, co už vyřešila.

Peťa chce obojí stejně: po opravě zůstat, zelené, s tlačítkem Hotovo.

## Proč anomálie mizí (ověřeno v kódu)

Dvě příčiny naráz, obě v `modules/erp/api/router.py`:

1. **Oprava/storno anomálii rovnou „vyřeší".** Endpointy `att_fix_entry` (~20707),
   `att_fix_void` (~20914) a `att_fix_merge` (~21083) nastaví
   `att_anomaly.resolved_at = now()`. Fronta pak řádek skryje filtrem
   `a.resolved_at IS NULL`.
2. **Opravený/stornovaný záznam se stane `superseded`.** Fronta jde přes
   `JOIN att_entry e ON e.id = a.entry_id` a filtruje `e.status <> 'superseded'`,
   takže po zásahu řádek zmizí i touhle cestou.

Rozpory tohle nemají — `att_day_confirm.disputed=true` drží, dokud ho `/fix/resolve`
nezhasne. Proto zůstávají.

## Návrh — dvě změny, obě v `router.py`, žádná změna databáze

### 1. Nevyřešovat anomálii automaticky při opravě

Ve třech fix‑endpointech vypustit `UPDATE att_anomaly SET resolved_at=now()`.
Anomálie zůstane otevřená až do kliknutí **✓ Hotovo — z fronty** — to volá
`/fix/resolve`, který `resolved_at` nastaví (beze změny).

### 2. Ukázat i anomálii se superseded záznamem, když byl den opraven

Ve frontě (`att_fix_queue`, ~20389) změnit:

```
AND e.status <> 'superseded'
```
na
```
AND (e.status <> 'superseded' OR <opraveno>)
```

kde `<opraveno>` je **týž EXISTS**, který už rozsvěcí zelený štítek (manual_fix
záznam na dni NEBO audit na dni). Tedy: běžně stále skrýt anomálie s neplatným
záznamem, ale ty, které Peťa **opravila**, nechat svítit.

## Jak se to pak chová

| stav | fronta |
|---|---|
| před opravou | anomálie svítí (záznam aktivní) |
| po opravě / stornu | **zůstane, zeleně „✓ opraveno", tlačítko ✓ Hotovo — z fronty** |
| klik na Hotovo | `/fix/resolve` → `resolved_at` → zmizí |

Přesně jako u rozporů od lidí. **Frontend se měnit nemusí** — tlačítko „Hotovo —
z fronty" u anomálií už existuje (přidáno 21. 7.), jen se dnikdy neukázalo, protože
řádek do té doby zmizel.

## Rozsah a rizika

- `router.py`: 3 řádky pryč (auto‑resolve) + 1 řádek filtru upravit. Blue‑green,
  vratné.
- **`att_fix_add` (doplnění) se neřeší** — ten anomálii nikdy nevyřešoval a záznam
  neruší, takže se už dnes chová správně (zůstane, zezelená).
- **Drobnost k rozhodnutí:** anomálie teď budou čekat na ruční odkliknutí, takže se
  ve frontě můžou hromadit. Dnes je drží `ORDER BY entry_date DESC LIMIT 120`.
  Volitelně omezit „opravené" superseded anomálie na posledních ~60 dnů (jako mají
  rozpory) — ať staré vyřízené nezacláněj. Doporučuju přidat, je to jeden `AND`.

## Staré opravené — červené upozornění (Peťa 22. 7.)

Peťa: *„předpokládám, že je vždy odkliknu, ale klidně tam tu podmínku dej — a ukaž
tam, kdyby to dělal někdy nějaký dareba, info o tom, že jsou tam nějaké staré,
červené drobné písmo někam, aby se pak nevymlouval, že se mu to ztratilo a on to
neví."*

Zapracováno:

- opravené anomálie **starší 60 dnů** se z hlavní fronty schovají (ať se nezanáší)
- dole se ale drobným **červeným písmem** hlásí: *„⚠ N opravených nesrovnalostí
  starších 60 dnů čeká na odkliknutí (skryté) — zobrazit"*
- klik na text je rozbalí i s tlačítkem **✓ Hotovo — z fronty**, takže jdou dořešit
- backend je vrací zvlášť jako `stare_skryte`, respektuje působnost editora

Nikdo se tak nevymluví, že o nich neví.

## Stav: HOTOVO V KÓDU, čeká na nasazení

- `router.py`: 3× vypuštěn auto‑resolve (fix/entry, fix/void, fix/merge) + upraven
  filtr fronty + přidán dotaz `stare` a klíč `stare_skryte`
- `dochazka-opravy.html`: sekce s červeným upozorněním na staré
- syntaxe ověřena (py_compile + JS)
- **Pozor při nasazení:** přes most běží i mzdová práce (paralelní session).
  Nenasazovat naslepo, ať se deploye nekříží.
