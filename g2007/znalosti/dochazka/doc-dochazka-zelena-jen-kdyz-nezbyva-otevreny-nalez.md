# Zelená v Opravách svítila, i když v dni zbývaly otevřené nálezy — detail i fronta (Peťa 9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 9. 9. 2026.** Peťa: *„divné je, že je to zelené — pokud je to chyba, mělo by to být červené."* A k frontě: *„pokud je něco špatně v detailu, nemůže to být vlevo zelené."*

Navazuje na pravidlo z 18. 8. 2026 (zelená = srovnáno, ne „někdo tu byl") a dotahuje ho na místa, kde dosud neplatilo.

## Co se dělo

Pavel Zeman, den 3. 9. 2026. Den měl DVĚ otevřené hlášky — chybí rozpad k úseku 13.00–16.56 a docházka 8,38 h proti rozpadu 4,45 h. Přesto:

- detail dne hlásil zeleně **„Co systému nesedělo — den je mezitím opravený"**,
- karty ve frontě vlevo měly zelený štítek **„opraveno"** a tlačítko „Hotovo — z fronty".

Důvod byl v obou případech stejný — stav se počítal z toho, že **v tom dni někdo něco opravoval** (`att_entry.source='manual_fix'` nebo záznam v `att_audit`), ne z toho, jestli ještě něco zbývá. Peťa ten den rozdělovala kvůli obědu, čímž ho „orazítkovala" jako opravovaný, a to přebilo i čerstvé nálezy.

## Oprava (nasazeno 9. 9. 2026)

**Detail dne** (`apps/api/static_db/dochazka-opravy.html`) — obě podmínky přepsané tak, že zelená smí svítit jen když nejsou žádné otevřené nálezy:

- `var _srovnano = !(j.anomalie||[]).length && !_maNeodhl;` (stav dne)
- `var _aok = !(j.anomalie||[]).length && !_maNeodhl;` (panel „Co systému nesedělo")

Do té doby tam bylo `(_byloOpraveno || ...)`, takže razítko o opravě zelenou rozsvítilo samo. Vedlejší nález — text **„Co systému nesedí — den se sice opravoval, ale pořád je co spravit"** byl v kódu dávno, ale nedosažitelný. Teď se konečně použije.

**Fronta** (`att_fix_queue`) — příznak `opraveno` se nepočítá u pravidel, která se při nočním úklidu SAMA zavírají, jakmile příčina zmizí: `chybi_zakazka`, `chybi_cinnost`, `chybi_rozpad`, `rozdil_dochazka_rozpad`, `pretazeni_useku`, `dva_bezici_naraz`, `sluzebni_cesta`, `zapomenuty_odchod`, `prazdny_den_doplnen`. Když je takový nález pořád otevřený, chyba TRVÁ a štítek by lhal. U ostatních pravidel (dlouhá směna, práce při absenci, budoucí záznam) se podmínka nepřepočítává, tam štítek zůstává jako nápověda k odbavení.

## Poučení

Stejné pravidlo bývá zadrátované na víc místech — stránka, datový podklad fronty, mobil. Když se mění chování barvy, projít všechna, ne jen to, kde si toho Peťa všimla.

Stránky z `g2007.soubor` se materializují na disk **při startu aplikace**, takže změna stránky se projeví až po deployi (restartu). Funkce v `g2007.python` se mění za běhu.

