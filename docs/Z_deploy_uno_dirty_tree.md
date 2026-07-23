# Deploy blokován „dirty working tree" — příčina a trvalý fix (-uno)

**Kdy:** 23.7.2026 (C23, hlášeno i Peťou nezávisle).

## Symptom
`/deploy/now` (i UI tlačítko, i most) hlásí:
`NENASAZENO: reason=dirty_working_tree — Cloud APP working tree neni clean, manualni intervence vyzadovana.`
Blokuje nasazování **celému týmu** (Claude instance i lidi). DB změny přitom jedou — jen se nenahrává kód.

## Příčina
Cloud APP repo `C:\Projekty\STRATEGIE` (na **EUR-APP-1P / 188.11**) měl **untracked** soubor
`modules/conversation/application/tool_registry/generated/audit_progress.py` — runtime‑generovaný.
`_git_working_tree_clean()` v `deployment_service.py` bral `git status --porcelain`, který zahrnuje
i **untracked** (`??`) → jakýkoli untracked soubor = „dirty" → deploy odmítnut. Přitom untracked
souboru reálný `git pull` vůbec nevadí (pokud nekoliduje s příchozím commitem).

## Trvalý fix (commit ee80b72a6)
`_git_working_tree_clean()` → `git status --porcelain -uno` (ignoruj untracked).
- Tracked/rozdělané změny dál blokují (správně — ty vyžadují pozornost).
- Untracked (generated/, logy, dočasné) už **neblokují nikoho**.
- Reálné kolize (příchozí commit chce přepsat untracked) řeší až `git pull` sám — s jasnou chybou.

## Jednorázové odblokování (když se to stane u staré verze kódu)
Na cloud APP boxu (EUR-APP-1P):
```
git -C C:\Projekty\STRATEGIE pull origin main   # přímý git obejde přísnou kontrolu; untracked mu nevadí
```
pak restart API. Přímý pull natáhne i tento fix, takže dál už blokovat nebude.

## Past: restart API a deploy token
`Restart-Service STRATEGIE-API` může app zvednout **bez env `STRATEGIE_DEPLOY_TOKEN`**, pokud token
není v perzistentní konfiguraci služby (byl jen v procesním env z původního spuštění). Pak token‑auth
(`/deploy/now`, `/diag-sql`, `X-Deploy-Token` endpointy) vrací `401 „Nejsi přihlášen"`.
- Během restartu je 401 i přechodně (app se zvedá ~5 s).
- Když přetrvá: dej `STRATEGIE_DEPLOY_TOKEN` do env služby a restartuj sankčním způsobem (ne holý Restart-Service).

## Prevence
- Kontrola stromu neblokuje na untracked (hotovo).
- Generované soubory (`**/generated/`, `*.pyc`, `__pycache__`) ideálně do `.gitignore`.
