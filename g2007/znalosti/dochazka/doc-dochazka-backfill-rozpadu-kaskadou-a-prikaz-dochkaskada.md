# Backfill rozpadu kaskádou — nový příkaz mostu @@DOCHKASKADA a srovnání srpna 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Navazuje na** `doc-dochazka-rozkol-hodiny-vs-casy-a-spousteni-kaskady` (proč docházka a rozpad
neseděly). Tohle je o **nástroji** a o **jednorázovém srovnání srpna 2026**.

## Nový příkaz mostu

`@@DOCHKASKADA <od> <do> [ostra]` — pustí kanonickou kaskádu (`att_fix_resync` →
`att_sync_vyroba_work`) přes rozsah dnů.

- **Bez slova `ostra` je to NÁHLED** (`dry_run`) — spočítá, co by se stalo, a nic nezapíše.
- Rozsah je omezen na 62 dnů (kontroluje `att_fix_resync`) — pouštěj po měsících.
- `create_missing` je natvrdo `false`, takže kaskáda **nezakládá** chybějící řádky rozpadu.
- Kaskáda si od 18. 8. 2026 sama hlídá zámek období (fail-closed).
- Most je token-auth bez session, takže ACL v `att_fix_resync` dostane `uid` Martiho (rodič) —
  `/diag-sql` je podle své vlastní dokumentace rodičovská cesta.

**Proč vznikl** (C24 + Kristý, 19. 8. 2026): backfill šel do té doby spustit **jen** přes API
endpoint `/app/attendance/fix/resync`, který nemá tlačítko v ERP ani příkaz na mostu — takže ho
fakticky neuměl spustit nikdo. Commity `4779cbb2` a `a0139324`.

**Gotcha:** most vykresluje jen `columns` a `rows`, vnořené JSON zahodí. První verze příkazu
vracela `JSONResponse(dict)` a v mostu se objevilo prázdné „0 řádků". Kdo přidává `@@` příkaz
s výstupem, musí vrátit `{"ok", "columns", "rows", "count"}`.

## Srovnání srpna 2026 (1.–18. 8., pustila C24 se souhlasem Kristý)

| Co | Kolik |
|---|---|
| dvojic člověk × den | 693 |
| dnů se změnou | 111 |
| ořez položky na hranice píchnutí | 179 |
| vypnuto — položka bez překryvu s docházkou | 21 |
| vypnuto — sousední duplicita | 7 |
| založeno nových | 0 |

**Ověřeno po zápisu:** druhý náhled hlásí nula změn (idempotentní) · přesahy položek přes
začátek píchnutí 0 (před během 9 u 4 lidí, 4,77 h) · nulové položky 0.

**Dnešek se schválně vynechal.** U lidí, kterým právě běží směna, položky nesou reálné hodiny
a bez uzavřeného dne vypadají jako „bez překryvu". Kaskáda je sice sama nechává být (běžící
den = konzervativní režim), ale do backfillu je zbytečné je tahat. Srovnají se večer samy,
protože od 18. 8. spouští kaskádu každé uzavření dne.

## Poučení — i „jednořádková" změna v automatu chce dopadovou mapu

Při opravě nesouměrnosti v `att_auto_checkout_midnight` (hlavičku zavíral podle jejího dne,
položky jen s dnešním datem — po půlnoci mu tak včerejšek propadl) byla první verze podmínky
příliš široká, „všechny otevřené položky do dneška". Do záběru tím spadlo **372 starých položek
ze staré Centrály** (30. 9. 2025 až 30. 6. 2026), kterým by noční automat připsal **4 835,7 h**,
včetně uzamčeného června. Chyba se chytla při ověřování, před nočním během, takže **nic
nezapsala**. Správné omezení je `source_system = 'app'` a jen včerejšek nebo dnešek.

Ponaučení do praxe: u změny v automatu se neptej jen „kompiluje se to", ale **„kolik řádků nově
spadne do záběru a co se jim stane"** — a odpověď si vytáhni dotazem, ne odhadem.

## Otevřené k rozhodnutí (stav 19. 8. 2026)

- **372 běžících položek ze staré Centrály** (`konec IS NULL`, `source_system='centrala1'`,
  9/2025 až 6/2026) — uzavřená množina k jednorázovému úklidu; automat je nevidí, ale narazí
  na ně každý, kdo bude zpracovávat starší období. Rozhodne Peťa (+ Jirka).
- **Pravidlo o parazitním úseku** v `att_wa_open` — přeformulovat z „úsek kratší než 60 s" na
  „úsek, na který se bezprostředně navazuje". Dnešní podoba umí sníst pauzu a po ořezu na celé
  minuty navíc nechává jednominutové útržky. Rozhodne Peťa.
- **Přepočet hodin za srpen** (drift z triggeru, cca −8,6 h za firmu) — mzdový dopad,
  schvaluje Marti.

