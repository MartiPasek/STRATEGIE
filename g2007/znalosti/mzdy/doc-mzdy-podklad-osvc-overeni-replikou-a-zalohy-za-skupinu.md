# Jak ověřit podklad OSVČ replikou v SQL — a proč se zálohy MUSÍ sčítat za skupinu

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Ověření podkladu OSVČ replikou v SQL

Claude-24 (Kristý), 2. 9. 2026. Vzniklo při kontrole podkladů Noska (425) a Voříška (327).
Navazuje na `doc-mzdy-podklad-osvc-dph-a-parovani-zaloh` a `doc-mzdy-podklad-osvc-vypocet-zakazek-final`.

## Proč to tu je

Kristý se ptala „jsou v podkladu zakázky, které tam být mají?“. Odpověď se dá dát jen
tak, že se podklad **znovu spočítá z databáze a porovná s vytištěným PDF**. Replika níže
sedí do koruny (Nosek: 42 řádků / 71 859 Kč zakázky + režie — přesně jako PDF).

## ⚠️ CHYBA, KTEROU JSEM UDĚLALA — zálohy per zakázka místo per skupina

Nejdřív jsem zálohy sečetla `WHERE cislo_zakazky = <zakázka>`. Vyšly mi čtyři zakázky,
které prý v podkladu chybí, a nahlásila jsem Kristý **4 105 Kč, které Noskovi propadnou.
Bylo to špatně.** Funkce (i Centrála) páruje zálohy **za celou skupinu sloučených zakázek**
(`tenant.oz_zakazky."_IDSkupiny"`). Po správném výpočtu:

| Zakázka | Skupina | Hrubě Kč | Už objednáno | Zbývá |
|---|---|---:|---:|---:|
| VR10390 | S:353 | 6 311 | 10 346 | −4 035 |
| VR10493 | S:323 | 262 | 974 | −712 |
| VR10602 | S:352 | 478 | 478 | 0 |
| VR10661 | S:372 | 350 | 350 | 0 |

Nikomu nic nepropadalo. **Poučení: každý dotaz, který odečítá zálohy, musí nejdřív
přeložit zakázku na skupinu.** Totéž platí pro „už vyplaceno“ v podkladu — např. VR10724
ukazuje 167 Kč, ačkoli na VR10724 žádná záloha není; leží na VR10673 ve stejné skupině 386.

## Klíč záloh (přesně jak to dělá kód)

```sql
WITH grp AS (
  SELECT "CisloZakazky" AS zak, 'S:'||"_IDSkupiny"::text AS g
  FROM tenant.oz_zakazky WHERE "_IDSkupiny" IS NOT NULL
), zal AS (
  SELECT z.cislo_zam AS cz, coalesce(g.g, z.cislo_zakazky) AS k,
         round(sum(coalesce(z.obj_bez_dph, z.vyplaceno)),0) AS uz
  FROM tenant.osvc_zaloha_zakazek z
  LEFT JOIN grp g ON g.zak = z.cislo_zakazky
  GROUP BY 1,2
)
```
Částka je `obj_bez_dph` s fallbackem na `vyplaceno` (bez DPH — viz doc o DPH).

## Hodiny přesně podle podkladu

Čtyři filtry, na které se snadno zapomene — bez nich součty nesednou:

```sql
FROM tenant.vyroba_work w
LEFT JOIN tenant.att_entry a ON a.id = w.att_entry_id
WHERE w.cislo_zam::text = :cz          -- NE user_id
  AND w.is_active
  AND w.konec IS NOT NULL              -- rozdělané píchnutí se nefakturuje
  AND (a.status IS NULL OR a.status <> 'superseded')
  AND w.fakturace_obj_id IS NULL
  AND w.datum <= :do
  AND w.zakazka_ref IS NOT NULL AND w.zakazka_ref NOT ILIKE 'Re_ie'
GROUP BY w.zakazka_ref
```
Režie se počítá zvlášť (`zakazka_ref ILIKE 'Re_ie' OR IS NULL`, mínus řádky shodné se
zdrojem dovolenkového `att_entry`).

## Větvení kandidátů (pořadí je závazné)

Kandidáti = zakázky s hodinami ∪ zakázky s otevřeným řádkem ve financích.

1. **je v `ec.zakazky_finance_zam`** (`id_pol_vobj IS NULL AND id_pol_pf IS NULL AND zbyva_vyplatit > 1`)
   → základ = `vyplatit` z financí (obsahuje prémii), typ **D**
2. **má jakýkoli řádek ve financích, ale vypořádaný** → PŘESKOČIT (jinak dvojí proplacení)
3. **`oz_zakazky."_Uzavreno" = true` a bez financí** → PŘESKOČIT (Centrála nefakturuje)
4. jinak hodiny × sazba, typ **D** když `_VyhodnoceniUzavreno`, jinak **Z**

Vyplatit = `round(základ) − round(zálohy za skupinu)`, tiskne se jen když > 1 Kč.
Sazba = `tenant.engagement.superhr_hod_bezfk`, poslední verze dle `valid_from` (NE `is_current`).

## Recency filtr je závislý na MCP — a tiše se vypne

Zakázka, která je jen ve financích a **nemá u nás hodiny**, se zahodí, pokud na ní člověk
posledních 12 měsíců nedělal (`EC_Dochazka` přes MCP). Když MCP neodpovídá, výjimka
nastaví `recent_zak = None` a **filtr se přeskočí bez chyby** — staré zakázky spadnou do
podkladu. Voříšek (327) má takhle čtyři kandidáty z let 2018–2022 v hodnotě 15 533 Kč
(VR8885, VR8890, VR8922, VR8120). Souvisí s `doc-mzdy-podklad-osvc-stare-zakazky-recency-filtr`.

**Při kontrole podkladu se proto vždy podívej, jestli v něm nejsou zakázky VR8xxx / staré
řady** — je to jediný snadno viditelný příznak, že filtr neproběhl.

## Ověřený stav k 2. 9. 2026

- **Nosek 425**: 42 řádků / 71 859 Kč + režie 11 807 Kč. Replika = PDF do koruny. Bez námitek.
- **Voříšek 327**: 9 řádků / 109 287 Kč + režie 10 122 Kč + 3 odměny 6 423 Kč = 125 832 Kč.
  Kristý ověřila, že staré VR8xxx v jeho podkladu nejsou. Bez námitek.

## Drobnost, která mate při porovnávání

Čísla se během dne hýbou — člověk pořád píchá. Voříškův i Noskův podklad seděl na hodinu,
kdy byl vytištěn; o dvacet minut později měl Nosek o 0,80 h režie víc. Při rozdílu do
desetin hodin hledej nejdřív časový posun, teprve pak chybu.

