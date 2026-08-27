# Hodinové sazby v Centrále: která je která a k čemu slouží (27. 8. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Hodinové sazby v Centrále — co je co

**Dohledala Peťa s Claude‑26, 27. 8. 2026.** Ověřeno na pěti lidech, vzorce sedí do haléře.

V `EC_FinZamPodminky` je hodinových sloupců dvanáct, ale **vyplněné jsou čtyři** (z 81 aktuálních lidí):

| Sloupec | Lidí | Co to je |
|---|---|---|
| `HrHodBezFK` | 75 | (základ + osobní ohodnocení) ÷ fond |
| **`HrHodsFK`** | 76 | (základ + osobní + individuální + **prémie**) ÷ fond |
| `ZakladZaHod` | 75 | `HrHodBezFK` **× 1,4** |
| `SuperhrHodsFK` | 76 | `HrHodsFK` **× 1,4** |

**Koeficient 1,4 je nákladový** — kolik hodina člověka stojí firmu. **U OSVČ se nepoužívá** (Havlát č. 105 má sazbu bez něj).

Fond = `PocetHodMes`, u plného úvazku 174 h, u zkráceného poměrně.

## K čemu slouží

- **`HrHodsFK` = sazba přesčasu.** Tuhle berou mzdy (`mzdy_loajalita_rows`, `payroll_raporty`). Pozor: **s FK**, ne `HrHodBezFK` — u 16 lidí se liší.
- **`ZakladZaHod` a `SuperhrHodsFK` slouží k oceňování práce na zakázkách**, ne k výplatám. Čtou je `EC_Zakazky_PrehledNakladu`, `EC_Zakazky_Spocitej`, `EC_Zakazky_VyhodnoceniUzavrit`, `EC_PrepocitejHospodareni_Prubezne` a funkce `EC_GetHodSazbaSuperHr`.

*(Procedury `hp_*`, které se v hledání taky objeví, jsou Heliosí vlastní — počítají superhrubou mzdu pro daně a s naším výpočtem nesouvisí.)*

## Nevyplněné sloupce

`OsOhodZaHod`, `VykonOhodZaHod`, `MzdaCelkemHod`, `MontazKcHod`, `CestaMontazKcHod` — nula lidí.

## Neověřeno

`SuperhrsFKSD`, `SuperhrsFKSDDN`, `SuperHrsFKSDReal` (76 / 76 / 75 lidí) **nejsou hodinovky** — jsou to částky v desítkách tisíc (70–110 tis.). Podle hodnot to vypadá na roční náklad na člověka se sick days a dovolenou navíc, `Real` přepočtený na skutečný úvazek. **Je to jen dohad z čísel**, počítá je `EC_FinZamPodmSpocitej`. Dohledává Šárka.

## Proč to tu je

Ve STRATEGII **žádná z těchto sazeb v Podmínkách není** — mzdy je berou ze zamrzlé kopie Centrály (76 sazeb ze 6. 8. 2026). Dokud se sazba přesčasu nedopočítá u nás, **snapshot se nesmí zrušit**. Ověřený vzorec pro dopočet je v [[doc-mzdy-zdroj-pravdy-podminky-misto-centraly]].

⚠️ Nepleť si to s **hodinovkou OSVČ**, kterou Šárka doplnila do Podmínek (`engagement.superhr_hod_bezfk`, 8 lidí, odpovídá `HrHodBezFK`). To je fakturační sazba živnostníků, ne sazba přesčasu zaměstnanců.

