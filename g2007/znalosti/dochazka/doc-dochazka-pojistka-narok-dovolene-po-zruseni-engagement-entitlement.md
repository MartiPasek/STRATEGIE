# Pojistka narok-dovolene-pravidla prepsana na Podminky (17.8.2026) - a proc pevna cisla v pojistkach nevydrzi

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se stalo

Pojistku `narok-dovolene-pravidla` zavedli **Peta + Claude-26** 3. 8. 2026. Zamer (jeji vlastni popis):
*"Musi existovat pravidla naroku na dovolenou (200 h + seniorita) a individualni naroky lidi - z toho se ma pocitat zustatek."*

Kontrola byla:
```
SELECT (SELECT count(*) FROM tenant.entitlement_rule WHERE tenant_id=2 AND active) >= 4
   AND (SELECT count(*) FROM tenant.engagement_entitlement WHERE tenant_id=2) > 1000
```

**16. 8. 2026** byla pri rozpadu dovolene na zakladni + navic tabulka `tenant.engagement_entitlement`
**smazana** (zustala `engagement_entitlement__zaloha_20260816`, 1926 radku); narok se od te doby cte
z Podminek `tenant.staff_cond`. Pojistka od te chvile hlasila **CHYBA KONTROLY** - tedy nespadla
tise do "ztraceno", ale prestala se dat vubec spustit. **Nehlidala nic** a slo o narok na dovolenou,
tedy o penize.

Nasel to Claude-28 17. 8. 2026 pri jine praci (kontroloval pojistky po svem zasahu a vsiml si, ze
pribyl nalez oproti vcerejsku).

## Jak je to opravene

```
SELECT (SELECT count(*) FROM tenant.entitlement_rule WHERE tenant_id=2 AND active) >= 4
   AND (SELECT count(DISTINCT user_id) FROM tenant.staff_cond
         WHERE tenant_id=2 AND scope_kind='user' AND cond_code='dovolena_zakladni_dni')
       >= (SELECT ceil(0.8 * count(*)) FROM tenant.att_employee
            WHERE tenant_id=2 AND is_active AND user_id IS NOT NULL)
```

**Zamer Pety zachovan** - dal se hlida, ze existuji pravidla naroku i individualni naroky lidi.
Zmenil se jen zdroj (Podminky misto smazane tabulky) a **pevne cislo se nahradilo podilem**.

### Proc podil a ne pevne cislo
Puvodnich `> 1000` bylo vazane na granularitu "radek na pracovni pomer a rok". Po prechodu na
Podminky je granularita "radek na cloveka a kod", takze stejne cislo uz nedava smysl. **Podil
funguje i kdyz firma vyroste nebo se zmensi** - pevne cislo je v pojistce vzdy jen odhad dnesniho
stavu a casem lze.

### Proc zrovna 80 procent (a ne "kazdy musi mit narok")
K 17. 8. 2026 ma narok **73 ze 78** aktivnich zamestnancu (93 %). Ti 4 bez naroku jsou
**Brigadnik Saxana, Demo Uzivatel, Marti-AI (user 2) a Martin Konicar (cislo 9038 = externi)** -
**zadny z nich narok mit nema**. Kontrola typu "kazdy aktivni zamestnanec musi mit narok" by proto
falesne rvala a lidi by si na ni zvykli jako na sum. Prah 80 % je zamerny polstar prave na tyhle
pripady; **tech zbylych max 20 % smi byt jen lide, kteri narok mit nemaji**. Marti-AI si vyzadala,
aby duvod prahu byl napsany primo v popisu pojistky - *"jinak pristi clovek nebude vedet, jestli je
prah zamerny nebo nahodny"*.

Soucet zakladni + navic se tu **zamerne nehlida** - to uz dela databazovy trigger, dublovat by bylo
zbytecne.

## Pouceni pro vsechny (tohle je to hlavni)

- **Kdyz rusis tabulku, projdi pojistky, ktere na ni sahaji.** Pojistka se nerozbila u autorky, ale
  u toho, kdo menil strukturu jinde. `SELECT kod, kontrola FROM tenant.pojistka WHERE kontrola ILIKE '%nazev_tabulky%'`
  je jednorazovy dotaz, ktery to odhali dopredu.
- **Rozdil mezi ❌ ZTRACENO a CHYBA KONTROLY je dulezity.** "Ztraceno" = hlidana vlastnost zmizela.
  "Chyba kontroly" = pojistka se ani nespusti, tedy **nehlida vubec** - to je horsi stav a snadno
  se prehledne, protoze v seznamu vypada jako dalsi radek.
- **Pevna cisla v pojistkach zestarnou.** Kde to jde, vazat na podil nebo na jinou tabulku, ne na
  konstantu.
- **Cizi pojistku opravit smis, kdyz hlida penize a je rozbita** - ale autora informuj hned potom
  a napis mu, CO a PROC jsi zmenil, ne jen ze je to opravene (postup schvalila Marti-AI 17. 8.).
  Peta informovana pres most tyz den.

Souvisi: [[doc-dochazka-mobile-command-payload-screen]] (druha pojistka zalozena tyz den)

