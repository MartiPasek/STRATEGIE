# Obsah webu a mobilu ma AUTOMATICKY archiv: g2007.soubor_historie + spoustec trg_soubor_archiv (prepsany obsah NENI ztraceny)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co to je (overeno v databazi 3. 9. 2026)

Nad tabulkou `g2007.soubor` (obsah webu a mobilni appky) je **zapnuty spoustec**
`trg_soubor_archiv`, ktery pri **kazde** zmene odklada predchozi verzi do tabulky
`g2007.soubor_historie`. Nikdo o tom nemusi vedet a nemusi nic delat - dela se to samo.

**Prakticky dopad pro celou sit:** kdyz nekdo prepise dilek mobilu a smaze tim cizi praci,
**stara verze NENI ztracena** - da se dohledat v historii podle casu.

## Jak to funguje presne

Telo funkce `fn_soubor_archiv_pred_update` (cteno pres `pg_get_functiondef`, 3. 9. 2026):

- Podminka: `OLD.obsah IS DISTINCT FROM NEW.obsah` **NEBO** `OLD.stav_zivota IS DISTINCT FROM NEW.stav_zivota`.
- Kdyz plati, vlozi do `g2007.soubor_historie` radek se **starym** obsahem
  (`soubor_id`, `kod`, `obsah`, `verze`, `stav_zivota`, `updated_by_uid`, `updated_by_text`,
  `platne_od` = puvodni `updated_at`, `nahrazeno_at` = `now()`).
- Zaroven **povysi `NEW.verze` o 1** a nastavi `NEW.updated_at = now()`.

**Funkce jen VKLADA. Zadny DELETE v ni neni.**

## Promazava to neco?

**Ne** - overeno 3. 9. 2026 trojim zpusobem:
1. v tele spoustece zadny DELETE neni,
2. v `g2007.automat` neni zadny zaznam zminujici `soubor_historie`,
3. v aktivnim `g2007.python` neni zadny vyskyt retezce `soubor_historie`.

Rozsah k 3. 9. 2026: **516 radku pro 50 ruznych souboru od 1. 8. 2026**;
z toho pro dilky mobilu 316 radku pro 29 souboru.

## Jak z historie cist

```sql
SELECT verze, length(obsah) AS znaku, md5(obsah) AS otisk,
       updated_by_text, platne_od, nahrazeno_at
FROM g2007.soubor_historie
WHERE kod = 'apps/api/static/mobile_parts/<soubor>'
ORDER BY nahrazeno_at DESC;
```

## Pozor - kdy to NESTACI

Historie je **spolecna a plni se i cizi praci**, takze navrat z ni znamena **hledat spravny
radek podle casu**. Kdyz se chystas na vetsi zasah, udelej si vedle toho jeste **pojmenovany
bod obnovy** - navrat z nej je jednim krokem.
Postup: `doc-system-strategie-bod-obnovy-pred-zasahem-do-obsahu-mobilu`.

Pozn.: sloupec `verze` v `g2007.soubor` je jen citac ziveho stavu, **historii nedrzi** -
tu drzi az tahle tabulka.

