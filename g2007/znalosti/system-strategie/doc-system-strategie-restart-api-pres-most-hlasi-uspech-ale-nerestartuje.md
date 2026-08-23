# Restart API přes most hlásí úspěch, ale aplikaci nerestartuje — ověřuj PID (23. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Restart API přes most hlásí úspěch, ale aplikaci nerestartuje

**Změřeno 23. 8. 2026** (Jirka + Claude-28, Mac, ve spolupráci s Marti-AI). **Dvakrát za sebou.**

## Co se děje

Operace `restart_service STRATEGIE-API` (OPS kanál mostu) vrátí:

```json
{"ok": true, "service": "STRATEGIE-API", "op": "restart", "tier": "green", "rc": 0, "out": "", "err": ""}
```

…ale **běžící aplikace se nerestartuje.** Ověřeno na PID:

| čas | akce | PID pythonu | start procesu |
|---|---|---|---|
| 21:10:12 | auto-deploy commitu `c3bddc90` | **4812** | 21:10:12 |
| 22:09 | `restart_service` → `rc: 0` | **4812** | 21:10:12 (nezměněno) |
| 22:52 | `restart_service` → `rc: 0` | **4812** | 21:10:12 (nezměněno) |

## Proč to nejde poznat z návratovky

Služba běží pod **NSSM** (`C:\Tools\nssm.exe`, není v PATH). Restart NSSM zabíjí a znovu spouští
**potomka** (python), ale sám běží dál. **`Get-Process` na PID služby proto vrací nssm, ne aplikaci** —
a jeho čas startu se nemění ani po korektním restartu. Je to past na dvakrát.

**Jak PID aplikace zjistit správně:**

```powershell
$p = (Get-CimInstance Win32_Service -Filter "Name='STRATEGIE-API'").ProcessId   # to je nssm
Get-CimInstance Win32_Process -Filter "ParentProcessId=$p" | Select ProcessId, Name, CreationDate
```

## Co restartuje spolehlivě

**Deploy.** Start 23. 8. ve 21:10:12 odpovídá auto-deployi commitu `c3bddc90` — to byl toho dne
jediný skutečný restart. Když je potřeba restart vynutit, jde to zatím jen přes nasazení.

## Proč na tom záleží

Cokoli, co se rozhoduje **jen jednou při startu**, zůstane po němém restartu ve starém stavu —
a navenek to vypadá, že se restart povedl. 23. 8. to stálo večer hledání: odesílací smyčka iOS
notifikací se při startu ve 21:10 rozhodla „APNs vypnuté" (klíč přišel až v 21:45) a dva „úspěšné"
restarty s tím nic neudělaly. Ruční `/test` přitom fungoval, protože si konfiguraci čte při každém
volání — takže to navenek vypadalo v pořádku. Detail: `doc-system-strategie-mobil-ios-notifikace-apns`.

> **Pravidlo: po restartu přes most vždy ověř PID potomka nebo jiný nezávislý příznak
> (log, uptime, chování). Návratovka `rc: 0` nic nedokazuje.**

## Dvě instance na EUR-APP-1P

| služba | adresář | port | role |
|---|---|---|---|
| `STRATEGIE-API` | `C:\Projekty\STRATEGIE` | 8002 | **primár** |
| `STRATEGIE-API-B` | `C:\Projekty\STRATEGIE-prev` | 8003 | sekundár |

Sekundár se v kódu pozná podle „prev" v cestě nebo podle `STRATEGIE_DR_STANDBY=1`
(`apps/api/main.py`, ~ř. 341) — **nikdy** podle `STRATEGIE_INSTANCE_NAME`.

**Na které instanci právě jsem** (bez přihlášení):
`GET /api/v1/health` → `{"instance":"primary","port":8002}` ·
`GET /api/v1/api-info` → navíc `commit`, `dir`, `stale`.

## Kde je log API

`C:\Logs\STRATEGIE\api-stdout.log` a `api-stderr.log` (pro B: `strategie-api-b.*`).
⚠️ **`api-stdout.log` má ~10 MB** a sype se do něj přístupový log, takže `-Tail 400` pokryje
jen pár minut — **hledat přes `Select-String` v celém souboru**, jinak to vypadá, že tam hláška není:

```powershell
Select-String -Path C:\Logs\STRATEGIE\api-stdout.log -Pattern "ios_push|lifespan" |
  Select-Object -Last 40 | ForEach-Object { $_.Line }
```

## Gotcha pro Mac

**OPS kanál mostu na Macu vůbec nefunguje** — volá PowerShell:
`exception: [Errno 2] No such file or directory: 'powershell'`.
Restart se z Macu tedy vyžádat nedá vůbec; musí ho udělat instance na Windows nebo Marti-AI.

