# Kontroly dochazky Centrala vs STRATEGIE: 5 mame, 7 nemame, 11 je mrtvych (parovani kus po kuse, 26. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Ktere kontroly dochazky mame a ktere ne

**Zmereno 26. 8. 2026 primo v datech obou databazi. Nic nebylo zmeneno.**
**Parovani je NAVRH, ne rozhodnuty stav** — potvrdit ma Dusan Havlat (vedouci vyroby).

## Zakladni cislo

Centrala ma v ciselniku `EC_Dochazka_ChybyVDochazceTypy` **23 druhu**, ale **11 z nich
za poslednich 12 mesicu nepadlo ani jednou**. Srovnava se tedy s **dvanacti**, ktere doopravdy
pracuji. STRATEGIE ma **10 druhu** (`tenant.att_anomaly.rule`).

**Z dvanacti pracujicich: 5 mame, 7 nemame.** Navic mame 7 kontrol, ktere Centrala vubec nema.

## MAME — 5 z 12

| c. | kontrola v Centrale | padlo za 12 mes. | u nas | co to je u nas |
|---|---|---|---|---|
| 4 | Neomluvena absence | 3 624 | **ano** | `neomluvena_absence` |
| 17 | Pozadavek na upravu | 307 | jinak | fronta oprav (`att_fix_request`) |
| 8 | Neukonceny den | 266 | zcasti | `zapomenuty_odchod` |
| 1 | Neukocena prestavka | 80 | zcasti | `dlouha_pauza` |
| 22 | Automaticky generovany zaznam | 21 | zcasti | `prazdny_den_doplnen` |

## NEMAME — 7 z 12

| c. | kontrola v Centrale | padlo za 12 mes. | poznamka |
|---|---|---|---|
| 6 | Mezery v dochazce | 1 384 | mezera nad 5 minut |
| 3 | Malo hodin | 1 095 | limit pod 6 h, nastavitelny na cloveka, jen pracovni dny |
| 13 | Vypnuta kontrola | 588 | ma dochazku, ale nema zaplou kontrolu; **jestli takovy prepinac mame, NEOVERENO** |
| 24 | Sluzebni cesta bez cestaku | 217 | cinnost 9 vs. 113 |
| 5 | Prekryta dochazka | 162 | v jeden okamzik vic zaznamu na jednoho cloveka |
| 23 | Prihlaseni na vyhodnocene zakazce | 57 | |
| 18 | Vice obedu | 35 | **u nas nemuze nastat, dokud nerozlisujeme obed** |

## MRTVE V CENTRALE — 11, za 12 mesicu 0 nalezu

c. **2** Zapomenuty obed · **7** Neukoncena prestavka · **9** Neopravnena cinnost ·
**10** Kratky obed · **11** Automaticky prodlouzeny obed · **14** Dlouhy obed ·
**15** Oriznuti dochazky · **16** Dlouha svacina · **19** Dlouhe koureni ·
**20** Chybi kuracky pausal · **21** Prekrocena max doba cinnosti.

**Devet z nich je o obede, svacine nebo koureni** — a to STRATEGIE vubec nerozlisuje:
ve `tenant.att_entry_type` jsou v kategorii `break` **jen dva zaznamy**: `break` ("Prestavka")
a `day_end` ("Dnes uz se mnou nepocitej"). Rozdil je jen v poznamce u zaznamu
("kratka pauza" prumer 12 min vs. "pauza - provetrani/jidlo" prumer 35 min).

**Kopirovat 23 druhu 1:1 = zalozit 11 polozek, ktere nikdy nic nenajdou.**

## MAME NAVIC — 7 kontrol, ktere Centrala nema

`nepotvrzeny_den` · `dlouha_smena` · `prace_pri_absenci` · `budouci_zaznam` · `chybi_zakazka` ·
`rozdil_dochazka_rozpad` · `prazdny_den_doplnen` (ten je zcasti protejskem c. 22).

Nejblizsi protejsek `dlouha_smena` by byl c. 21 (Prekrocena max doba cinnosti), ale ten
v Centrale nikdy nepadl.

## Tri moznosti, jak postavit ciselnik (NEROZHODNUTO)

| | co se zalozi | pro | proti |
|---|---|---|---|
| **A** | nasich 10 druhu, ktere realne vznikaji | ciselnik odpovida tomu, co system opravdu dela | Dusan nenajde 7 kontrol, na ktere byl zvykly |
| **B** | vsech 23 z Centraly | uplna shoda se starym svetem | 11 mrtvych polozek od prvniho dne |
| **C** | nasich 10 + tech 7 chybejicich, ktere davaji smysl i u nas | zachova chybejici kontroly bez mrtvych polozek | musi se to jednou projit kus po kuse |

**Doporuceni (Claude-28): A jako start, C jako cil.** Rozhodnout ma Dusan — on vi, ktere
kontroly mu chybi. K 26. 8. 2026 se na nej ceka, nemel cas.

## Jak se to zmeri znovu

Centrala (`db=mssql`), pocty za 12 mesicu vcetne odmavnutych:
```
SELECT t.ID, t.Nazev, t.Popis, COUNT(c.ID) AS celkem,
       SUM(CASE WHEN c.DatPorizeni >= DATEADD(month,-12,GETDATE()) THEN 1 ELSE 0 END) AS za_12m,
       SUM(CASE WHEN c.ChybaJeOK = 1 THEN 1 ELSE 0 END) AS odmavnuto, MAX(c.DatPorizeni) AS naposledy
FROM EC_Dochazka_ChybyVDochazceTypy t
LEFT JOIN EC_Dochazka_ChybyVDochazce c ON c.Typ = t.ID
GROUP BY t.ID, t.Nazev, t.Popis ORDER BY t.ID;
```
STRATEGIE (`db=pg`): `SELECT rule, count(*), count(DISTINCT employee_id),
count(*) FILTER (WHERE resolved_at IS NULL) FROM tenant.att_anomaly GROUP BY rule;`

## Souvisi

- `doc-dochazka-anomaly-ciselnik-druhu-chyb-chybi` — proc u nas ciselnik neexistuje
- `doc-dochazka-centrala-nocni-kontrola-a-automaticke-opravy` — kdy kontrola bezi a co sama opravi
- `doc-dochazka-anomaly-frontu-nikdo-rucne-neodbavuje` — frontu nalezu nikdo neproklikava
- `doc-dochazka-prehled-cely-den-vv-centrala-rozbor` — prehled, kvuli kteremu se to resi

