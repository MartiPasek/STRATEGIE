# 🧾 Píchatelnost zakázek: co je `_DochPrihlaseni` a proč na něj nefiltrovat

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Autor: Claude‑28 (Jirka), 20. 7. 2026. Podnět: Pavel Voříšek — „v appce nejde zvolit
zakázka VR10669 pro zahájení práce". Ověřeno proti DB_EC i produkční PG, opraveno
commitem `82ab045f`.

## 1. Hlavní věta (kdyby sis přečetl jen jeden odstavec)

**`TabZakazka_EXT._DochPrihlaseni` NENÍ povolení píchat na zakázku.** Je to **odvozený
příznak**, který si Centrála nastaví **sama**, jakmile se na zakázku někdo **poprvé**
píchne. Kdo ho použije jako podmínku „smí se na to píchat", vyrobí past 22: **novou
zakázku půjde v STRATEGII zahájit až poté, co ji někdo zahájí ve staré Centrále.**

## 2. Důkaz (procedura `EC_DochazkaMultif` v DB_EC)

Uvnitř procedury, která zakládá docházkový záznam, je od 23. 1. 2024 tohle:

```sql
--jiri 23.1.2024 - pokud existuje zakazka bez zapisu z dochazky, zapsat přihlášení a datum
IF exists(select top 1 1 from TabZakazka Z
          left outer join TabZakazka_ext ZE ON ZE.ID=Z.ID
          where Z.CisloZakazky=@CisloZakazky and isnull(ZE._DochPrihlaseni,0)=0)
BEGIN
  update Ze set Ze._DochPrihlaseni=1, Ze._DochPrihlaseniDatum=ZakazkaDochazka.DatumPripadu
  from TabZakazka Z left outer join TabZakazka_ext Ze on ZE.id=Z.id
  OUTER APPLY (SELECT TOP 1 D.ID, D.DatumPripadu FROM EC_Dochazka D
               WHERE D.CisloZakazky=Z.CisloZakazky ORDER BY D.DatumPripadu asc) as ZakazkaDochazka
  where Z.CisloZakazky=@CisloZakazky
END
```

Čili: příznak + datum se plní **zpětně z prvního docházkového záznamu**. Je to evidence
„na téhle zakázce se už někdy pracovalo", ne konfigurace.

## 3. Jak se to projevilo (případ VR10669, 20. 7. 2026)

| Čas | Událost |
|---|---|
| do 9:05 | `_DochPrihlaseni=0` → v `tenant.zakazka` `pichatelna=false` → **Pavel ji v appce nevidí** |
| 9:05:24 | zaměstnanec č. 488 se na ni píchne **ve staré Centrále** → procedura flipne příznak na 1 |
| 9:12:37 | automat `sync_zakazky` (à 30 min) → `pichatelna=true` |
| po 9:12 | zakázka je v appce, 23. v pořadí |

**Dopad nebyl ojedinělý.** V okamžiku nálezu bylo otevřených (nezrušených, neuzavřených,
neukončených) zakázek **246**, ale appka jich nabízela **jen 66** — zbylých **180**
skrývala jen proto, že se na nich zatím nikdo nepíchl.

## 4. Platné pravidlo (od 20. 7. 2026)

Zdroj: `_sync_zakazky_from_helios()` v `modules/erp/api/router.py`.

**Píchatelná = `_Uzavreno=0 ∧ _Zruseno=0 ∧ Ukonceno=0`.** Podmínka na `_DochPrihlaseni`
je pryč (v kódu je u parametru `"pi"` komentář proč — ať ji někdo „nevrátí zpátky jako
chybějící"). Ověřeno po syncu: **246 píchatelných**, VR10669 mezi nimi.

## 5. Gotchy k tomuhle zrcadlu (ať je nikdo neobjevuje znovu)

- **Sync je plný mirror, ne přírůstek.** Nejdřív `UPDATE tenant.zakazka SET pichatelna=false
  WHERE tenant_id=2`, pak upsert otevřeného setu. Co v Centrále zhasne, zhasne i tady —
  ruční `UPDATE pichatelna=true` v PG proto **nepřežije nejbližší sync**. Opravovat se musí
  v Centrále nebo v podmínce syncu.
- **Interval 30 min** (`fw.mirror_job`, `job_key='sync_zakazky'`). Po zásahu v Centrále
  není zakázka v appce hned — až po dalším běhu. Kdo nechce čekat, pustí ⚙ ops akci
  `sync_zakazky` (řídící centrum).
- **Picker `/api/v1/erp/app/zakazky` má `LIMIT 100`** (do 20. 7. jen 30) a řadí
  `(typ='REZIE') DESC, cislo DESC`. Při 246 zakázkách je vyhledávání běžná cesta — hledá se
  `ILIKE %q%` přes číslo i název, takže **`VR 10669` s mezerou nenajde nic**, `10669` ano.
- **`typ` se odvozuje z prefixu čísla** (`VR`/`SW`/`PR`, `REZ`→`REZIE`, jinak `OST`), není
  to údaj z Heliosu.
- **Píchatelnost se vynucuje i při zápisu**, ne jen v pickeru — `checkin` i ruční opravy
  časů ověřují `pichatelna=true` a jinak vrátí „Zakázka X není píchatelná / neexistuje."

## 6. Obecné poučení

Příznaky v `_EXT` tabulkách Centrály vypadají jako konfigurace, ale často jsou to **stopy
po provozu** (kdy se co poprvé stalo). Než se takový sloupec použije jako podmínka, vyplatí
se ověřit, **kdo ho zapisuje** — `SELECT o.name FROM sys.sql_modules m JOIN sys.objects o
ON o.object_id=m.object_id WHERE m.definition LIKE '%_NazevSloupce%'` odpoví za pár vteřin.
