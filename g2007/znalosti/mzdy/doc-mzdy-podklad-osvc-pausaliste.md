# Podklad fakturace OSVC: pausaliste (Hodinovka=0) - jak to resi Centrala a co z toho plyne pro STRATEGII

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Pausaliste v podkladu fakturace OSVC (Hodinovka = 0)

Claude-24 (Kristy), 19. 8. 2026. Zdroj = procedura Centraly
`EC_Zakazky_GenPodkladFakturace_Priprava` (precteno 19.8.2026, 561 radku).

## Pravidlo Centraly

Prepinac je **`EC_FinZamPodminky.Hodinovka`** (bit), bere se z radku `Aktualni = 1`:

```sql
SELECT @Hodinovka = Hodinovka FROM EC_FinZamPodminky WHERE CisloZam = @CisloZam and Aktualni = 1
```

- **`Hodinovka = 1` (hodinar)** — castka radku = `EC_ZakazkyFinanceZam.Vyplatit`
  (hodiny x sazba); radek se ukaze, kdyz `Vyplatit - uz objednano > 1`.
- **`Hodinovka = 0` (pausalista)** — castka radku = **`EC_ZakazkyFinanceZam.FixPremie`**
  misto `Vyplatit`; radek se ukaze, kdyz `FixPremie - uz objednano > 1`.

A hlavne: pausalistovi se po naplneni tabulek **smazou vsechny radky z doch1zky**:

```sql
IF ISNULL(@Hodinovka,0) = 0
BEGIN
  DELETE ##TempPodkladFakturace WHERE AUTOR = SUSER_SNAME() and (typ <> 1 OR DatUzavreni < '2023-07-01')
  DELETE ##TempPodkladFakturaceRezie WHERE AUTOR = SUSER_SNAME()
END
```

Tedy pausalistovi **NEJDE do podkladu ANI JEDNA HODINA A ANI REŽIE** — zustanou jen
radky typ 1 (z `EC_ZakazkyFinanceZam`) s `DatumPorizeni >= 1. 7. 2023` a k tomu odmeny.
Komentar v procedure (Swobi 5.10.2023): *"Na zadost Martina proplacet Pausalistum
neplacenym od hodiny od druheho pololeti 2023 odmeny za zakazky. Nyni se nastavovalo
kvuli Dusanovi, ale neni to nikde omezene jeho cislem."*

## Kdo je pausalista (stav 19.8.2026)

Z dilenskych OSVC (`DruhSmlouvy=3`) je pausalista **jediny Dusan Havlat (105)**.
Mimo dilensky seznam ma `Hodinovka=0` dalsich 15 OSVC (349 Sik + rada cisel 9xxx).

**Ve STRATEGII uz ten priznak JE**: `tenant.engagement.hodinovka` je **boolean** a sedi
s Centralou (105 = false, ostatnich 7 aktivnich dilenskych OSVC = true). Nic se nemusi
doplnovat, jen se podle nej musi vypocet rozvetvit.

## Co z toho plyne pro Fazi 1 (jeste NENI hotove)

- Novy vypocet `podklad_vyplaceni_pdf_faze1` zatim pocita **vsem stejne z hodin** — u Havlata
  proto vyhodil 497 733 Kc (1 093 h nefakturovane rezie x 385). Podle pravidla Centraly
  mu ale rezie ani hodiny nepatri vubec.
- Stary (interim) vypocet byl u nej jeste hur: scital nefakturovanou rezii z Centraly az
  do 2022 a vysel na 2 991 452 Kc. Ty 2 321 radku rezie v Centrale nejsou dluh - jsou to
  radky, ktere se u pausalisty do fakturace **nikdy nedostanou** (procedura je maze).
- **Zdroj pro pausalisty je uz zrcadleny**: `ec.zakazky_finance_zam` (1:1 `EC_ZakazkyFinanceZam`,
  23 479 radku / 255 lidi) ma i `fix_premie`, `vyplatit`, `zbyva_vyplatit`, `id_pol_vobj`,
  `id_pol_pf`, `datum_porizeni`. Havlat ma 1 368 radku; po pravidle Centraly
  (datum_porizeni >= 7/2023, bez VOBJ/PF, zbyva_vyplatit > 1) vychazi `fix_premie` 46 200 Kc,
  z toho k fakturaci **0 Kc** (uz objednano to pokryva) + odmeny.

## Pozor pri dopocitavani "uz objednano"

Procedura Centraly bere objednane **z `TabPohybyZbozi.CCSDPHKC`** napojene pres
`EC_Zakazky_PlatbyZam.IDPolVobj` (a pres skupiny slouceni zakazek `TabZakazka_EXT._IDSkupiny`),
NE pres `EC_Zakazky_PlatbyZam.Vyplaceno`, jak to dela dnesni interim i nove zrcadlo
`tenant.osvc_zaloha_zakazek`. U hodinaru to zatim sedelo, ale u sporu o koruny je tohle
prvni misto, kam se podivat. Sloucene zakazky (skupiny) dnes nova logika neresi vubec.

## HOTOVO 19. 8. 2026 - vetev pausalisty v kandidatu

`g2007.python` **`podklad_vyplaceni_pdf_faze1`** (verze 2, md5 45c5ca250985e10776c1b6b296ca5d32)
uz pravidlo Centraly implementuje:

- prepinac = `tenant.engagement.hodinovka` z POSLEDNI verze engagement (stejny radek, ze ktereho
  se bere `superhr_hod_bezfk`); NULL se bere jako hodinar (pojistka pro novy zaznam),
- pausalista: `hrs = []`, `rez_work_h = 0`, `dov_h = 0` -> zadne hodiny, zadna rezie, zadna dovolena,
- misto toho radky z `ec.zakazky_finance_zam`: `id_pol_vobj IS NULL AND id_pol_pf IS NULL
  AND COALESCE(zbyva_vyplatit,0) > 1 AND datum_porizeni >= DATE '2023-07-01'`
  a `cislo_zakazky NOT IN ('Režie','Rezie','Sklad','VKM','Sdružená')`;
  castka radku = `fix_premie` minus uz objednano (ze zrcadla `osvc_zaloha_zakazek`), tiskne se pri > 1 Kc,
- odmeny beze zmeny (spolecne pro obe vetve),
- u pausalisty se meni patka PDF i hlavicka Excelu ("pausal - neni placen od hodiny"),
  sazba se u nej nikde neuvadi a chybejici/nulova sazba u nej NENI chyba (422 plati jen hodinarum).

**Overeno spustenim pres `@@PYRUN` (19.8.2026):**

| clovek | vysledek |
|---|---|
| Havlat 105 (pausalista) | **6 921 Kc, 1 radek** - jen "Jednorazove odmeny od vedouciho" (`ec.pripl_srazky` id 19940, 7/2026). Zadne hodiny, zadna rezie; z FixPremie neprosel zadny radek (od 7/2023 je `fix_premie` 46 200 Kc, ale uz objednano to cele pokryva). Pro srovnani: interim v8 mu ukazoval 2 991 452 Kc. |
| Erhard 372 (hodinar) | 196 503 Kc, 14 radku - **beze zmeny** proti verzi bez pausalni vetve (regrese OK) |
| Kilberger 346 (hodinar) | 102 557 Kc, 5 radku - **beze zmeny** (regrese OK) |

Ostry kod `podklad_vyplaceni_pdf` je porad v8 (nezmenen) - prepnuti ceka na Kristy.

