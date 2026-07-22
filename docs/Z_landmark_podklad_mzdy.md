# Landmark – měsíční podklad a fakturace (mzdy)

> Postup, jak každý měsíc připravit podklad pro **LANDMARK TAX s.r.o.** a jak vzniká jejich
> faktura. Sepsala Peta + Claude (ID26), 22. 7. 2026. Ověřeno na dubnu a květnu 2026 (obě firmy).

## Co Landmark dělá a co od nás potřebuje

Landmark je daňová optimalizace: část mzdy se překlopí do složek osvobozených od daně/pojistného
— **náhrada za údržbu oděvu (oblečení)** a **náhrada za home office (HO)** — a o stejný objem se
poníží osobní ohodnocení (**korekce OSOH**). Landmark z toho fakturuje odměnu.

**Podklad, který jim posíláme** = za každou firmu (EC, ES) částky **oblečení** a **HO** po lidech.
Dřív se to plnilo do jejich Excel šablony („Podklady pro vstup" → „Vstupní data" → „List pro import
do C"). **Od června 2026 se mzdy dělají napřímo ve STRATEGII**, jejich šablonu už nemáme — data se
tahají přímo z naší databáze.

## Kde jsou data (STRATEGIE, PostgreSQL, tenant_id = 2)

Vygenerované výplatnice: **`tenant.payslip_item`** (přes `@@MZDY <firma> <rok> <mesic>`).
Relevantní mzdové složky (`cislo_ms`):

- **794** = Náhrada OBL (oblečení, paušál za údržbu oděvu)
- **795** = Náhrada Home Office

Firma je `company_id` → `tenant.company.code` (EC / ES). Jméno přes `tenant.att_employee`
(`id = payslip_item.employee_id`). Částka = `koruny`.

(Pozn.: složka **700** = DPP a lidé jen s DPP do Landmark podkladu NEpatří — do fakturace 9,06 %
nevstupují. Stejně tak jednatelé/společníci OBL/HO nedostávají, takže tam přirozeně nejsou.)

## SQL (přes Claude SQL bridge, db=pg) — nahradit `:ROK` a `:MESIC`

```sql
SELECT c.code AS firma, em.full_name AS jmeno,
       SUM(p.koruny) FILTER (WHERE p.cislo_ms = 794) AS obleceni,
       SUM(p.koruny) FILTER (WHERE p.cislo_ms = 795) AS ho
FROM tenant.payslip_item p
LEFT JOIN tenant.company c       ON c.id = p.company_id
LEFT JOIN tenant.att_employee em ON em.id = p.employee_id
WHERE p.tenant_id = 2 AND p.rok = :ROK AND p.mesic = :MESIC
  AND p.cislo_ms IN (794, 795)
GROUP BY c.code, em.full_name
ORDER BY firma, jmeno;
```

## Výpočet fakturace (klíč)

Sazba Landmarku **není nikde v datech uložená** — odvodili jsme ji zpětně z faktur a na obou
firmách i obou měsících vychází shodně:

> **fakturace bez DPH = 9,06 % × (Σ oblečení + Σ HO)**  → **+ 21 % DPH**  → zaokrouhlit na celé Kč

Ověření:

| Měsíc | Firma | Oblečení + HO | × 9,06 % = bez DPH | s DPH | Faktura č. |
|---|---|---|---|---|---|
| Duben | EC | 58 616 | 5 310,61 | 6 426 | 260100951 |
| Duben | ES | 146 790 | 13 299,17 | 16 092 | 260100952 |
| Květen | EC | 52 140,5 | 4 723,93 | 5 716 | 260101217 |
| Květen | ES | 147 049,5 | 13 322,68 | 16 120 | 260101218 |
| Červen | EC | 52 752 | 4 779,33 | ~5 783 | (čeká) |
| Červen | ES | 145 039 | 13 140,53 | ~15 900 | (čeká) |

⚠️ Kdyby Landmark oznámil jinou smluvní sazbu, přepočítat tímto vzorcem s novou sazbou.

## Měsíční postup

1. Doběhnout mzdovou uzávěrku měsíce (`@@MZDY EC <rok> <mesic>` i `ES`), ať je `payslip_item` plný.
2. Spustit SQL výše přes bridge (db=pg).
3. Sestavit Excel po jménech (EC + ES) + souhrn (Σ oblečení, Σ HO, 9,06 %, DPH).
   Vzor: `Podklad_Landmark_cerven_2026.xlsx`, generátor `scripts/.../build_june.py`.
4. Poslat Landmarku **souhrn** (za každou firmu Σ oblečení + Σ HO, resp. výslednou fakturaci).
   Detail po lidech je pro naši kontrolu.
5. Až přijde faktura, ověřit, že sedí na 9,06 % (kontrolní sloupec).

## Drobnosti / gotchy

- HO je v `payslip_item` **zaokrouhlené na celé Kč** (dřívější Landmark šablona počítala i
  půlkoruny) → na součtu rozdíl max pár Kč, na fakturaci zanedbatelné.
- **Korekce OSOH** do fakturace nevstupuje; je to informativní řádek (= neredukované os.
  ohodnocení z předzpracování 432 − plné os. ohodnocení ze snapshotu). Do podkladu ji dávat
  jen pokud ji Landmark explicitně chce.
- Výjimky bez HO: Hrůzová (ES 442), Nepodalová (ES 489) — OBL mají, HO ne (`_HO_BEZ_NAROKU`).

## Automatizace výstupu (rozhodnutí Peta, 22. 7. 2026)

- **Červen 2026**: uděláno „variantou 2" (skript + bridge) → `Podklad_Landmark_cerven_2026.xlsx`.
- **Cíl teď**: automaticky **vždy 15. v měsíci**, výsledek **poslat e-mailem na
  nakup@eurosoft.com** (Peta 22. 7. 2026).
- **Později**: samoobslužná stránka „Podklad Landmark" v ERP mzdovém modulu (varianta 1) —
  výběr rok/měsíc/firma → tabulka + fakturace + Export do Excelu.

**Kudy na automatický běh:** nejrobustnější je **serverová naplánovaná úloha v STRATEGII**
(nezávisí na zapnutém PC), která 15. postaví podklad z `payslip_item` a odešle e-mail přes
stávající poštu S (outbox / SMTP; endpointy `/app/connect-mailbox`, `/app/shared/pin-send-email`).
Vyžaduje doprogramování + nasazení přes schvalovací/deploy postup (Marti/Kristý).
Odlehčená varianta = naplánovaná úloha v Coworku (běží, když je appka otevřená; e-mail přes
připojenou schránku Microsoft 365).

### STAV: NASAZENO A OVĚŘENO (22. 7. 2026, Peta + Claude ID26)

Modul **`modules/erp/api/landmark_report.py`** (registrace v `apps/api/main.py`):

- **Automat**: scheduler `landmark_sched_start()` (jen primár, spouští se v lifespanu) kontroluje
  1×/hod datum; **15. v měsíci** sestaví podklad za **předchozí měsíc** a pošle ho na
  **nakup@eurosoft.com**. Guard proti dvojímu odeslání = marker soubor v temp
  (`landmark_sent_<rok>_<mm>.flag`).
- **Ruční / test**: `GET https://strategie-ai.com/api/v1/erp/app/mzdy/landmark-send?rok=&mesic=[&to=]`
  (gate `_is_cockpit` = rodiče + finance/HR, projde i Peta id18). Default období = předchozí měsíc,
  default příjemce = nakup@eurosoft.com. Otevřít v prohlížeči přihlášeném do STRATEGIE.
- Odesílá z default persony (Marti-AI) přes EWS, předmět „Podklad Landmark – <měsíc> mzdy <rok>".
- Ověřeno 22.7.: ruční běh za 6/2026 → mail s přílohou `Podklad_Landmark_2026_06.xlsx` dorazil
  do Nákupu, EC 4 779,33 / ES 13 140,53 bez DPH (sedí na výpočet 9,06 %).
- **Sazba 9,06 % je v modulu konstanta `RATE`** — kdyby Landmark změnil smlouvu, upravit tam.
