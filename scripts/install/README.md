# Instalační skripty služeb STRATEGIE

**Doplněno 9. 9. 2026** (zadal Jirka Honomichl, schválila Marti-AI msg 15104 pro celý blok).
Do té doby **pět služeb nemělo žádný instalační postup** — kdyby se aplikační server stavěl
znovu, musely by se poskládat ručně z hlavy. Nastavení v těchto skriptech není vymyšlené:
je **opsané ze skutečně běžících služeb** na aplikačním serveru (čteno z registru 8. 9. 2026).

## Co který skript staví

| skript | služba | stroj | co dělá |
|---|---|---|---|
| `install_strategie_api.ps1` | STRATEGIE-API | app 188.11 | hlavní aplikace (port 8002) |
| `install_strategie_caddy.ps1` | STRATEGIE-CADDY | app 188.11 | brána — HTTPS a směrování |
| `install_strategie_task_worker.ps1` | STRATEGIE-TASK-WORKER | app 188.11 | fronta úloh (SMS, e-maily, přepis hlasu) |
| `install_strategie_email_fetcher.ps1` | STRATEGIE-EMAIL-FETCHER | app 188.11 | stahování pošty do schránek person |
| `install_strategie_restart_watcher.ps1` | STRATEGIE-RESTART-WATCHER | app 188.11 | restart po nasazení + srovnání zálohy |
| `_spolecne.ps1` | — | — | sdílené funkce, samo se nespouští |

**Jinde už skripty byly** a tyto je nenahrazují: záložní verze aplikace
(`../install_strategie_api_b*.ps1`), most (`../setup_claude_instance.ps1`),
hlídač obnov na datovém serveru (`../setup_apid_watcher_service.ps1`),
MCP v Plzni (`../install_eurosoft_mcp_on_ec_server2.ps1`),
testovací prostředí (`../setup_api_d.ps1`).

## Jak je pouštět

Na **aplikačním serveru**, v PowerShellu **jako správce**:

```powershell
cd C:\Projekty\STRATEGIE\scripts\install
.\install_strategie_api.ps1 -Promenne @{ STRATEGIE_DEPLOY_TOKEN='...' }
```

- **Jsou opakovatelné.** Když služba existuje, jen srovnají nastavení; když ne, založí ji.
- Bez práv správce se samy zastaví. Když nenajdou, co potřebují (python, caddy, složku),
  řeknou to lidsky a nic neudělají — vyzkoušeno.
- `-Nespoustet` nastavení jen zapíše a službu nespustí.

## ⛔ Tajemství do těchto skriptů nepatří

Tokeny, hesla a klíče **v žádném z nich nejsou a nikdy být nesmí** — leží v gitu, do kterého
vidí celá síť. Předávají se parametrem `-Promenne` jako dvojice název = hodnota.
Stejný princip má i starší `../setup_claude_instance.ps1`.

Když `-Promenne` vynecháš, **už nastavené proměnné zůstanou beze změny** — takže se
opakovaným spuštěním nedá omylem přijít o přihlašovací údaje.

> **Proč na to takový důraz:** 8. 9. 2026 se při zjišťování tohoto nastavení omylem
> dostaly do souborů na disku skutečné hodnoty tří tajemství (nasazovací token, klíč
> k trezoru a heslo k databázovému serveru). Musely se odstranit ručně. Názvy proměnných
> jsou neškodné, hodnoty ne.
