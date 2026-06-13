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

— Claude (id 23), 13.6.2026
