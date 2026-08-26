# Správa docházky: co je žádost a co den, kde sedí fajfka a na co působí akce z menu

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Správa docházky — žádost vs. den, fajfka vedoucího, na co působí akce z menu

**26. 8. 2026, Peťa + C26.** Vzniklo z toho, že se v přehledu obojí plete a hromadná akce
hlásila „není označena žádná žádost", i když řádky označené byly.

## Dvě různé věci na jedné obrazovce

| | **Žádost** | **Den** |
|---|---|---|
| Co to je | papír — někdo si dopředu řekl o volno, čeká na rozhodnutí | skutečný záznam docházky, počítá se do mzdy |
| Tabulka | `tenant.att_absence_request` | `tenant.att_entry` |
| Poznávací znamení v přehledu | sloupec **Zdroj** = „žádost z appky" | Zdroj = appka, ruční oprava, schválená žádost, plán z Centrály, import z Centrály, neschopenka ČSSZ |
| Identita řádku (`RadekId`) | `Z:<id žádosti>` | `D:<id>,<id>,…` |
| Co znamená fajfka ve sloupci S | žádost je ve stavu `approved` | `att_entry.ved_schvaleno` = vedoucí to viděl a odsouhlasil (hodiny to nemění) |

**Žádost NENÍ podmínkou dne.** Den v docházce vzniká i bez schválení (ohlášení z appky,
plán, sync z Centrály, ruční zápis) — pravidlo Peti z 30. 7. 2026, viz
`doc-dochazka-sprava-vs-new-co-se-preklapi`. Schvalování běží vedle.

## Jeden řádek přehledu může nést víc dnů
Denní větev datasetu `dochazka.zakazky_budoucnost_list` slepuje souvislé dny do jednoho
řádku a jejich id skládá do `string_agg(DISTINCT entry_id::text, ',')`. Řádek „Hrůzová,
dovolená 1.–7. 8., 5 D" tedy nese **pět** `att_entry` (1. a 2. 8. byl víkend).
Fajfka nemá kam se uložit „za období" — zapisuje se na každý den zvlášť.

**Pozor na `bool_or`:** fajfka u slepeného řádku se rozsvítí, když ji má **aspoň jeden**
den z bloku. Částečně odfajfkovaný blok vypadá jako hotový. Rozpad je vidět až v Docházce
new (sloupec `VedSchvaleno`) nebo v datech.

## Na co působí akce z kontextového menu (Peťa 26. 8. 2026)
`window.akceRadky()` v `dochazka-po-zakazkach.html`:
- **nic označeného** → akce vezme řádek, na kterém člověk stojí (`CTX_ROW`),
- **označeno víc řádků** → vezmou se označené, `CTX_ROW` se ignoruje.

`Schválit označené` / `Vzít schválení zpět` umí obojí naráz: co je `Z:`, rozhodne přes
`/app/attendance/absence/decide`; co je `D:`, odfajfkuje přes
`/app/dochazka-zak-tab/save-doch-meta` (`ved_schvaleno`), a to pro každý den v řádku.

## Kde se `ved_schvaleno` zapisuje
1. `att_absence_decide` při schválení žádosti — celý blok naráz (od 6. 8. 2026),
2. správcovská cesta ve Správě docházky (`dochazka_absence_sprava._zapis_dny`) podle
   zaškrtávátka „Schváleno",
3. `save-doch-meta` po jednom řádku (Docházka new, Opravy, nově hromadná akce),
4. přepočty (`att_dovolena_kaskada`).

## Doložená nesrovnalost a její příčina (26. 8. 2026)
Nápravný běh **18. 8. 2026 v 6:19** doplnil fajfky jen dnům **do 31. 7.** — srpnové nechal
být. Proto vznikly „částečně odfajfkované" bloky: každý blok, který přetéká přes konec
července. Doloženo na žádostech 19 (Hladíková, fajfka 29.–31. 7., chybí 3. 8.) a 22
(Hrůzová, fajfka 27.–31. 7., chybí 3.–7. 8.). Stav před opravou: 58 bloků kompletních,
14 zcela bez fajfky, 2 částečné.

Opraveno 26. 8. 2026 (6 dnů) — doplněno jen tam, kde je žádost `approved`. Zbylých 28 dnů
u 14 žádostí fajfku **nemá správně**: ty žádosti pořád čekají na rozhodnutí (11 z nich má
vedoucího Dušana Havláta, dále Šik pod Kristýnou, Šafránková ml. pod Michelle, Čepický pod
Petrem Benešem). Fajfka se jim doplní sama, až se rozhodnou.

## Otevřené
- **Den a žádost o sobě navzájem nevědí, když den vznikl z ohlášení.** Odkaz (`source_id`
  + `source_system='absence_req'`) nese jen den vytvořený SCHVÁLENÍM. Když si člověk
  ohlásí absenci v appce, den vznikne rovnou, ale bez vazby — a když pak ohlášení zruší,
  den zůstane viset a musí ho ručně stornovat člověk. Doloženo: Jiří Honomichl, lékař
  19. 8. (záznam 10009312, ohlášeno 17. 8. 4:42, stornováno ručně 25. 8. s poznámkou
  „zaměstnanec to zrušil, záznam zůstal viset kvůli chybějící vazbě na žádost").
- Zvážit, zda fajfku u slepeného řádku neukazovat až při `bool_and` místo `bool_or`.
  Peťa 26. 8.: částečné bloky nemají vznikat, takže lepší je opravit data než zobrazení.

