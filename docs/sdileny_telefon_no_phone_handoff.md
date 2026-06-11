# Sdílený telefon — diagnóza `no_phone` + návrh řešení

**Handoff pro Marti / Claude-23** · od Claude (přes Kristý) · 11. 6. 2026

> ⚠️ **Důležité upozornění o zdroji:** Tohle jsem psal z dev-checkoutu, který je
> **~396 commitů / 6 dní pozadu** (zamrzlý na 5. 6.), a sandbox neměl přístup na
> GitHub ani na cloud → **aktuální kód „sdíleného telefonu" jsem nečetl.** Odkazy
> na kód níže (`OnboardingSession`, `primary_phone`) jsou ze starší verze a slouží
> jen jako vodítko — ověřte si přesné místo v aktuálním kódu. Vy jste na téhle
> funkci pracovali dnes (poslední commit `fix(nastaveni): doplnit chybějící řádek
> "Sdílený telefon" do nastavení`), takže nejspíš víte přesně, kde enrollment + PIN žije.

---

## Kontext / problém

Kristý nastavuje **sdílený telefon** (mobil, PWA) — jeden fyzický telefon + jedna
instalace appky pro víc lidí. Scénář:

1. Přidává sebe + kolegyni na **jeden** sdílený, **už ověřený** telefon.
2. „Přidat lidi" proběhne — kolegyni vidí na obrazovce.
3. „Nastavit PIN → poslat SMS kód" skončí chybou: **`no_phone` — „Tento user nemá
   ověřený mobil"**.

**Cíl Kristý (potvrzeno):** obě mají používat sdílený telefon **bez stálého
přihlašování/odhlašování**. Kolegyně **nemá** mít vlastní ověřené číslo — **sdílený
(už ověřený) telefon má pokrýt obě.**

---

## Diagnóza

- Krok „poslat SMS kód" je **onboarding ověření nového uživatele přes SMS na jeho
  vlastní číslo** (ve staré verzi model `OnboardingSession.sms_code` +
  `sms_code_expires_at` + `is_verified`).
- Backend hledá u cílového uživatele (kolegyně) **aktivní/ověřený telefonní
  kontakt** (vzor v `modules/auth/api/router.py` ~ř. 302–377: `primary_phone`;
  pokud `None` → větev „no phone" / email fallback, log `sms_requested_no_phone_contact`).
- Kolegyně žádný ověřený telefonní kontakt nemá → **`no_phone`**.
- Samotný řetězec `no_phone` jsem ve webovém kódu nenašel jako literál — text hlášky
  skládá nejspíš UI vrstva (PWA). Backendová **podmínka** (cílový user musí mít
  ověřené vlastní číslo) je ale jádro problému.
- Nativní appka (`APP/Mobile`, Kotlin) řeší jen telefonování + aktualizace —
  **žádnou správu uživatelů ani PIN.** Flow „Nastavit PIN / přidat lidi" je tedy
  ve **webové PWA**.

### Hlubší příčina UX
Web/PWA rozlišuje uživatele přes **cookies**, a ty jsou v jednom prohlížeči/originu
**společné** — dva lidé tedy nemůžou být přihlášení naráz (okomentované přímo v
`index.html`). **PIN-přepínání je přesně na tohle**, ale enrollment druhého
uživatele pořád vyžaduje **per-user ověření jeho čísla**, což u sdíleného telefonu
(kolegyně své číslo nepoužívá) padá.

---

## Návrh řešení

Na zařízení, které je **už důvěryhodné** (`TrustedDevice` / platný `device_token`),
umožnit **rodiči** (`is_marti_parent`) zapsat PIN druhého uživatele **bez kroku
„poslat SMS kód"**.

**Gate — musí platit všechno současně:**
- požadavek podává **přihlášený rodič** (`is_marti_parent == True`),
- probíhá to na **už-trusted zařízení** (platný `device_token`),
- akce se **zapíše do auditu** (kdo, koho přidal, na jaké zařízení, kdy) →
  `fw.diag_log` / activity log.

Pokud gate projde, enrollment vytvoří/aktivuje PIN druhého uživatele **rovnou
(skip SMS)** — za uživatele ručí rodič a zařízení je fyzicky důvěryhodné.

**Bezpečnostní logika:** důvěra je přenesená přes (a) fyzicky důvěryhodné zařízení
a (b) rodiče, který akci vědomě autorizuje — odpovídá doktríně *„důvěra je v
subjekt"* + rodičovská autorita. SMS ověření **vlastního** čísla je pro tenhle
případ nadbytečné, protože kolegyně to číslo nepoužívá. Plošně se nic nerozvolní —
gate je úzký a auditovaný.

### Alternativa (pokud nechcete měnit enrollment logiku)
Poslat ověřovací SMS na **číslo sdíleného telefonu** (číslo zařízení/SIM), ne na
číslo kolegyně. Funguje, ale je složitější (musíte znát/držet číslo zařízení) a
neřeší to obecně — proto doporučuju spíš ten gate výše.

---

## Otevřené otázky pro vás (potřebuju k přesné implementaci)

1. Kde přesně je v **aktuálním** kódu endpoint „Nastavit PIN / poslat SMS kód"
   (PWA → backend)? Ve staré verzi to vedlo na onboarding/auth.
2. Kde je uložený **PIN** a vazba `device ↔ user ↔ PIN`? V mé staré verzi PIN model
   nebyl — je nejspíš nový (z těch 396 commitů).
3. Souhlas s gate **rodič + trusted device + audit**, nebo chcete jiný model důvěry?
4. Má být PIN enrollment bez SMS dostupný **jen rodiči**, nebo i adminovi / běžnému
   ověřenému uživateli na trusted device?

Jakmile mi dáte aktuální kód (nebo přesné soubory/endpoint), dotáhnu backendovou
část s vámi.

---

## Mezitím — workaround pro Kristý

Bez zásahu do kódu se „obě bez přihlašování" čistě udělat **nedá** (cookies per
origin). Dočasně: kolegyně se na sdíleném telefonu **jednorázově přihlásí přes svůj
e-mail (magic link)**, když potřebuje. Je to přesně to otravné přepínání, které
řešíme — proto ten enrollment fix.

---

*Pozn.: dokument vznikl při testování na cloudu (strategie-ai.com). Diagnóza
vychází ze staršího kódu + chování v UI; přesné názvy v aktuálním kódu prosím
ověřte.*
