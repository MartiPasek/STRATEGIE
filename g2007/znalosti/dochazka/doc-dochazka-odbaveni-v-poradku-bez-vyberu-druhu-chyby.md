# V pořádku se nesmí ptát na druh chyby a musí jít zmáčknout i u červeného nálezu

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# „V pořádku" se nesmí ptát na druh chyby — a musí jít zmáčknout i u červeného nálezu

**Peťa + Claude-26, 28. 8. 2026.** Nasazeno, `apps/api/static_db/dochazka-opravy.html` v69.

## Pravidlo (Peťa)
*„Když říkám v pořádku, nevybírám přece druh chyby."* Odbavení nálezu, který po kontrole
chybou není, je **jedno kliknutí s pevným důvodem** — ne formulář.

## Co bylo špatně

### 1) Fronta chtěla vybrat druh chyby
Tlačítko **„✓ V pořádku — vyřídit"** u nesrovnalostí volalo `resolveUI()`, které rozbalilo
`reasonBox()` s nadpisem *„Důvod (povinný)"* a sedmi tlačítky ze seznamu `REASONS`:
*zapomenutý odchod, zapomenutý návrat z pauzy, zapomenutý příchod, zapomenutý oběd/pauza,
mezera v docházce, chybný typ záznamu, omylem založený záznam.* To jsou **druhy chyb** —
a když je nález v pořádku (typicky legitimní dlouhá pauza), žádný z nich neplatí.

Server důvod nikdy nevyžadoval (`att_fix_resolve` uloží prázdný jako `-`); povinnost byla
jen v UI.

**Oprava:** nová funkce `okUI()` pošle rovnou `{anomaly_id, reason:'zkontrolováno — v pořádku'}`.
Vzor byl už v témž souboru — odbavení v detailu dne to tak dělalo od 19. 8.

### 2) V detailu dne šlo odbavit jen modrý nález
Tlačítko **„✓ V pořádku — odbavit"** se kreslilo jen pod podmínkou `_ainfo`, tedy pouze
u **modré** hlášky („člověk si to upravil sám" / „konec už je doplněný"). U **červené**
hlášky se nevykreslilo vůbec — a den, jako je *„pracovní den bez docházky i bez absence"*,
tak neměl v detailu jak potvrdit. Jediná cesta vedla přes kartu ve frontě, kde si to
vyžádalo ten výběr druhu chyby.

**Oprava:** podmínka změněna z `_ainfo` na `!_aok && !_maNeodhl` — tlačítko je vždy, když
je co odbavit. Zůstává skryté, když na dni visí **neodhlášený záznam**; tam se nejdřív
musí doplnit konec.

## Kde to je
`apps/api/static_db/dochazka-opravy.html` (žije v `g2007.soubor`, v gitu NENÍ):
`okUI()` u ř. 408, tlačítko fronty ř. 460, podmínka detailu dne ř. 1013.

## Poznámka pro příště
Nabídku `REASONS` používají i další místa toho souboru (storno, sloučení, převod dne) —
tam je výběr druhu chyby na místě, protože se opravdu opravuje. Nesahat na ni plošně.

