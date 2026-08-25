# Absence se vede BEZ ČASU — jedinou výjimkou je Lékař (18. 8. / 25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Absence se vede BEZ ČASU — jedinou výjimkou je Lékař

**Rozhodla Peťa 18. 8. 2026. Poslední díra dořešena 25. 8. 2026 (Peťa + Claude-26).**

## Co platí

- Dovolená, dovolená navíc, sick day, OČR, nemoc, neplacené volno i ostatní absence se vedou
  **na celý nebo půl dne, BEZ ČASU**. Sloupce `started_at` a `ended_at` zůstávají prázdné.
- **Jediná výjimka je Lékař** — leží uvnitř pracovního dne mezi píchnutími a čas se mu dopočítává
  z mezery v docházce (`/app/dochazka-abs/najdi-mezeru`, Peťa 12. 8. 2026).
- Na hodiny, FPD ani mzdy to nemá vliv — sdílený výpočet `tenant.att_den_hodiny` u absencí časy
  vůbec nečte, sčítá jen `hours`.

## Proč

Umělý rámec dne dělal **falešné překryvy s píchnutou docházkou**. Peťa 18. 8. 2026 doslova:
„v opravě docházky se nemá co opravovat čas, maximálně měnit z celého dne na půl den, takže ty
časy by tam naopak mohly být zavádějící, dala bych je všude pryč." V Centrále se absence taky
vede na den nebo půl dne, ne na čas.

## ⛔ CO PŘESTALO PLATIT — neber to jako pravidlo

1. **Rámec „od šesté ranní"** (platil do 12. 8. 2026) — ZRUŠENO.
2. **Rámec „8.00 až 8.00 + denní úvazek"** (12.–18. 8. 2026) — ZRUŠENO.
3. **Komentář v uloženém dotazu** `fw.data_set` kód `dochazka.zakazky_budoucnost_list`,
   podepsaný „Peta 12.8.2026", který zněl „Bereme rámec jako v Centrále, 8.00 až 8.00 + denní
   úvazek (typicky 8-16)" — **NEPLATÍ**, přepsáno 25. 8. 2026. Peťa k tomu 25. 8. výslovně
   uvedla, že časy nezadáváme vůbec, a ne kvůli sobotě.

## Kde to bylo rozbité (nález 25. 8. 2026)

Rozhodnutí z 18. 8. se promítlo jen do jedné ze dvou zapisovacích cest.

- `dochazka_absence_sprava.py` → `_zapis_dny` — opraveno už 18. 8. 2026.
- **`g2007.python` kód `att_absence_decide`** (schválení žádosti vedoucím) — **zůstalo po staru**
  a zapisovalo rámec od šesté ranní dál. Poslední takový záznam vznikl 25. 8. 2026 v 5.11 ráno.
  Opraveno 25. 8. — zapisuje prázdno.
- **Přehled Správa docházky** (`fw.data_set` kód `dochazka.zakazky_budoucnost_list`) si čas navíc
  **dopočítával** na 8.00 až 16.00, když žádný nenašel — ukazoval tedy čas, který v datech vůbec
  není. Zrušeno 25. 8., záloha `tenant.zaloha_data_set_budoucnost_20260825`.

## Úklid dat

25. 8. 2026 smazány časy u 21 dovolených; záloha `tenant.zaloha_absence_casy_20260825` (22 řádků
včetně opravy Beneše). Lékaři ponechány — 95 záznamů s časem zůstalo nedotčeno.

## Hlídá to pojistka

`tenant.pojistka` kód `absence-bez-casu-krome-lekare` — kontroluje zároveň data, schvalovací
cestu i přehled. Když se kterákoli z těch tří věcí vrátí, pojistka se ozve.

