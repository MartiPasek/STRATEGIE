# Teamio (Jobs.cz / Práce.cz) — co zařídit u LMC v pondělí

Stav: systém ve STRATEGII je **připravený na API**, čeká jen na přístupy od LMC/Alma Career.

## Co je hotové (13.6., Claude‑23)
- `tenant.recruit_posting` — tabulka inzerátů (živá).
- Appka → **Nábor → 📣 Inzeráty → Jobs.cz / Práce.cz**: zakládání/úprava inzerátu,
  tlačítko **📤 Publikovat** a **📥 Stáhnout uchazeče** (zatím hlásí „čeká na přístup").
- Klient na **Vacancies Import API** (POST form‑urlencoded `xmlString`, schéma onrea/ei_std_jd)
  a stub na **Replies Export API** (uchazeči zpět).

## Co potřebujeme od LMC (Šárka v pondělí)
1. **Aktivovat na Teamio účtu EUROSOFTu:**
   - službu **Automatický import inzerátů** (Vacancies Import API),
   - službu **Export odpovědí / uchazečů** (Candidate Applications Export / Replies Export API).
2. LMC vydá **přístupy (url + username + password)** pro každou službu. Import URL bude
   tvaru `https://g2.lmc.cz/import/<custompath>/import`.
3. Případně **ID prezentační jednotky** firmy (`<presentationUnit id="…">`), pokud chceme
   inzeráty pod brandovanou prezentací.

## Co pak udělá Claude (po předání přístupů)
- Vložení přístupů do `AppEnvironmentExtra` (proměnné `TEAMIO_IMPORT_URL/USER/PASS`
  a `TEAMIO_REPLIES_URL/USER/PASS`) — secret zadá Marti, ne Claude.
- Ostrý test: 1 inzerát do Teamia (draft) → ověření v Teamiu → publikace.
- Dotažení parseru uchazečů (Replies Export XML → `recruit_candidate`/`recruit_application`,
  dedup e‑mail, GDPR dle docs) + scheduled pull.
- Doladění číselníků (profese/lokalita/úvazek) dle Teamio codebooku (test tool LMC).

## Odkazy
- Přehled API: https://integrations.almacareer.com/teamio/
- Import inzerátů: https://integrations.almacareer.com/teamio/vacancies-import-api/
- Export uchazečů: https://integrations.almacareer.com/teamio/replies-export-api/
- Codebooky/test tool: https://integrations.almacareer.com/teamio/vacancies-import-api/tools-schemas-value-lists/test-tool/

## Pipeline uchazeči (Teamio → STRATEGIE) — návrh + stav (15.6.2026)

Cíl (Marti): po příchodu uchazeče do Teamia **bez ruční práce** → okamžitá notifikace
s předvyplněnými údaji + ihned přívětivá auto-odpověď uchazeči.

**Replies Export API** (ověřeno z dokumentace):
- `GET <URL>?login=&password=&type=3` (+ `from/until/fromTime/untilTime`), default 5 dní,
  max 200/volání, min 60 s mezi voláními (plán: scheduled á 30 min).
- XML `candidateList → candidate`: jméno, e-mail, telefon, `pdjdId` (inzerát), recruiter,
  reakce, zdroj, GDPR (platnost), přílohy Base64. Typy: CV 208700001/010, motivační 208700013,
  ostatní 208700002, dotazník JOF/Flexi 208700004/003.

**Hotovo 15.6.:** `modules/erp/api/teamio_replies.py` — parser **OVĚŘEN** na vzorovém XML
(jméno, e-mail, telefon, inzerát, GDPR, klasifikace příloh CV/cover/form + Base64 dekód).
`build_url()/fetch_replies()` čtou env (inertní bez přístupů).

**Zbývá dostavět (po přístupech od LMC):**
1. Upsert `recruit_candidate` (dedup e-mail) + `recruit_application` (inzerát/stav/reakce/zdroj/GDPR).
2. CV → uložit do složky (EUROSOFT RW zóna) + **OCR/extrakce** (PDF→text→LLM předvyplní kartu).
3. **Notifikace** na mobil „nový uchazeč na [pozici]" s předvyplněnými údaji.
4. **Auto-odpověď uchazeči — bod 5 (Marti):** ihned automaticky **přívětivá odpověď**
   („děkujeme, Šárka se vám ozve, jak to půjde" — PR na 1. místě), s **vypínačem** auto-odpovědi.
   (Začít rovnou A = automaticky; vypínač per inzerát/globálně.)
5. Scheduled pull á 30 min + dedup (`teamio_candidate_id`), GDPR: po expiraci souhlasu anonymizovat
   (dle `docs/nabor_personalistika_v2.md`).

**Gating:** ostrý běh až po `TEAMIO_REPLIES_URL/USER/PASS` (Šárka zařizuje u LMC; Marti vloží do
AppEnvironmentExtra). Parser otestovatelný i bez nich.

— Claude (id 23), 13.6.2026 · pipeline uchazeči + parser 15.6.2026
