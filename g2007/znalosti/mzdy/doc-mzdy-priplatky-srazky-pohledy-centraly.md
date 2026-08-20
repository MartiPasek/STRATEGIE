# Priplatky a srazky: jak jsou pohledy (pojisteni/tarif/kvalita) v Centrale SKUTECNE definovane + oprava chybneho zaveru z 27.7.

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Priplatky a srazky - pohledy Centraly, overeno primo v definicich (C28, 29. 7. 2026)

> oblast: `mzdy` - Claude-28 (Jirka). Navazuje na [[doc-mzdy-priplatky-srazky]] a [[doc-mzdy-priplatky-srazky-ui-27-7]].
> Podnet: Jirka nesouhlasil se zaverem "pojisteni je jen text v poznamce" a chtel to poradne overit. Mel pravdu.

## 1. OPRAVA CHYBNEHO ZAVERU

Znalost `doc-mzdy-priplatky-srazky-ui-27-7` tvrdi: *"pojisteni neni druh odmeny - je to jen text v poznamce"*.
**To je SPATNE.** Zaver vznikl z prohledavani katalogu typu a poznamek, ne z definice pohledu.

## 2. KDE POHLEDY CENTRALY DOOPRAVDY ZIJI

Tabulka **`EC_DELPHI_TabObecnyPrehled`** (sloupce `Cislo`, `Nazev`, `DefView` = SQL prehledu).
NE `EC_ViewSeznam` (tam k priplatkum neni nic) a NE `EC_PrehledyFiltryUziv`.
Doprovodna `EC_DELPHI_TabObecnyPrehledPodminky` je jen podmineny FORMAT (barvy/font), ne filtr.

Prehledy nad `EC_FinPriplatkySrazkyDefinice`:

| Cislo | Nazev | Filtr (skutecny WHERE) |
|---|---|---|
| 1080 | MZDY-Priplatky/Srazky/... | hlavni prehled |
| 1078 | ... vse | bez omezeni typu |
| 1111 | ... jadro | editacni formular |
| 1048 | ... kvalita | `F.Typ = 30` |
| 1114 | ... telefonni tarif | `F.Typ IN (4, 43)` |
| **1116** | **... pojisteni** | **`F.Autor LIKE 'JKlikova'`** |
| 1117 / 1119 | odmeny zapoctene hod. sazbou (loni / letos) | detail per zaznam |
| 1118 | Grid sumace do hod. sazby | sumace |

**Pohled "pojisteni" tedy nefiltruje podle pojisteni, ale podle AUTORA zaznamu** - ukazuje, co zalozila
Jana Klikova. Vraci 3 radky (ID 11160, 14640, 18623), vsechny Mares Mirek c. 9005 (OSVC), typ 7
"Jednorazove odmeny od vedouciho", poznamka "Pojisteni odpovednosti pro EUROSOFT-Control", roky 2024-2026.
Jana Klikova uz ve firme neni (`att_employee` c. 18, `is_active=false`) -> pohled se prestal plnit.
**Pri prevodu do STRATEGIE ho NEKOPIRUJ 1:1** - je to mrtvy filtr. Zadani si vyzadej od Petry
(dotaz odeslan mailem 29. 7. 2026 15:05).

Pohled "kvalita" (typ 30 = Korekce osobniho ohodnoceni (kvalita)) nema za 2025-2026 jediny zaznam.

## 3. VYRESENA NESROVNALOST "Vyplaceno" (Petin dotaz z 27. 7.)

Petra poslala snimek, kde maji 3 radky zaskrtnute `Vyplaceno` + datum, ale v tabulce je
`Vyplaceno=0` a `DatVyplaceni` NULL. Znalost ui-27-7 to nechavala jako "nevysvetleno".
**Vysvetleni: prehled 1116 si oba sloupce DOPOCITAVA** z navazane polozky prijate faktury:

```
DatVyplaceni = ISNULL(F.DatVyplaceni, P.DatPorizeni)
Vyplaceno    = convert(bit, CASE WHEN ISNULL(P.CCBEZDANIKC, F.Vyplaceno) > 0 THEN 1 ELSE 0 END)
...
LEFT OUTER JOIN TabPohybyZbozi P ON F.IDPolPF = P.ID
OUTER APPLY (SELECT DruhSmlouvyText FROM EC_FinZamPodminky ...) Smlouva   -- odtud sloupec "Smlouva" HPP/OSVC
```

Overeno na tech 3 radcich: faktury 1169751 / 1212410 / 1279677 s `DatPorizeni`
04.04.2024 / 18.12.2024 / 31.03.2026 - **presne data z Petina snimku**. Nic v datech neni rozbite.

## 4. DUSLEDEK PRO CUTOVER: fakturacni vetev

Vazba `IDPolPF` (polozka prijate faktury) a `IDPolVobj` (polozka vydane objednavky) je pouzivana siroce:
2024 = 230 radku, 2025 = 212, 2026 = 61. **Nejsou to jen OSVC** - tech 61 radku patri 15 lidem
(mj. Dusan Havlat, Marek Honal, Pavel Vorisek, Jiri Honomichl), typy 5, 7, 9, 13, 20, 23, 36, 43, 44.
Vsech 15 lidi uz v STRATEGII existuje vcetne engagementu - neni koho zakladat.

`tenant.wage_movement` tuhle vazbu **nema** a nerozlisuje kanal (mzda / faktura / objednavka).
Ledger `tenant.zamestnanecky_zavazek` uz sloupec `kanal` ma a komentar v `router.py:34322` rika,
ze faktura/objednavka jsou zamysleny "na pozdeji". Jirka rozhodl 29. 7.: **OSVC i HPP resit najednou**,
tj. kanal protahnout az do `wage_movement`.

## 5. UPLNY KATALOG TYPU (aby se na zadny nezapomnelo)

V Centrale je **49 typu** (`EC_FinPriplatkySrazkyDefiniceTypy`), za 2025-2026 se realne pouziva **22**,
`TYP_MAP` v `_sync_priplatky_from_ec()` pokryva **14**.

**Chybi a v datech 2025-26 REALNE JSOU:** 1 DPP-polozka (5x, MS 700, reakce=true), 11 Doplatek (1x, 651, true),
12 Prispevek za ziskani pracovnika-pohovor (1x, 651, true), **27 Vanocni premie (64x, 651, true - vraci se
v prosinci!)**, 28 Odmeny IT (4x, 651, true), 34 Fakturace-rucni zadani (28x, false), 42 OSVC korekce (1x, false),
43 Telefonni tarif OSVC (35x, false).

**Existuji s ReakceMzdy=true, ale bez zaznamu 2025-26** (mohou se vratit): 2, 3, 17 Odmena Jednatel (693),
18 Rocni zuctovani dane (97), 29, 35, 39, 41; neaktivni 6, 14, 15, 16.

## 6. GOTCHY (usetri cas)

1. **Diakritika z MSSQL pres most**: `CAST(sloupec AS varchar(N)) COLLATE SQL_Latin1_General_CP1251_CI_AS`
   vrati ciste ASCII bez hacku misto rozsypaneho `OdmÄ›na`. Funguje spolehlive.
2. **Velky text pres most = HTTP 401 "Nejsi prihlasen"**, i kdyz je dotaz spravny. Limit je nizsi, nez se zda:
   1 radek x 250 znaku projde, 5 x 300 uz ne. Dlouhe `DefView` tahej po ~230-250 znakovych kouscich
   (`SUBSTRING`), nebo rovnou jen `WHERE` cast pres `CHARINDEX('WHERE', ...)`.
3. **Diakritika DO PG pres most**: `convert_from(decode('<base64>','base64'),'UTF8')` - jediny spolehlivy zpusob.
   Pouzito i pro odeslani ceskeho e-mailu pres `public.email_outbox`.
4. **Odeslani e-mailu bez UI**: INSERT do `public.email_outbox` (status='pending', from_identity='persona',
   persona_id=1 = Marti-AI, ktera jako jedina ma podpis). Worker `flush_outbox_pending` (sluzba
   STRATEGIE-EMAIL-FETCHER) ho odesle sam. Plain text se prevadi na HTML vcetne markdownu.
   Overeno 29. 7. 2026: mail Petre odeslan v 15:05 na prvni pokus.

## 7. Marek Honal - vyreseno 29. 7. 2026

Mapovani `garant_odmena -> HELIOS 651` doplneno (`wage_system_mapping` id 19, request #1521 schvalil Jirka
14:45). Overeno pruchodem stejnymi podminkami, jake pouziva `_mzdy_priplatky_rows`: radek 19917
(Marek Honal, 250 Kc, 7/2026, approved, MS 651) do cervencove mzdy **projde**.

## Navaznosti
- [[doc-mzdy-priplatky-srazky]] - modul · [[doc-mzdy-priplatky-srazky-cutover-praha]] - rozhodnuti a plan
- [[doc-mzdy-priplatky-srazky-ui-27-7]] - UI uprava (par. "pojisteni" je timto OPRAVEN)

