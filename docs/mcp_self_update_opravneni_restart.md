# EUROSOFT-MCP — bezobslužný `@@MCPUPDATE` (oprávnění k restartu služby)

**Stav:** `@@MCPUPDATE` udělá `git pull` + zkopíruje `.py` do pkg složky, ale **nová
verze se nenačte bez skutečného restartu služby** (běžící Python proces má starý
modul v paměti; přepsání souboru na disku samo o sobě nic nezmění). Self-update
proto spouští odpojený PowerShell, který má službu `Stop → copy → Start`. Ten krok
**tiše selhává** → po `@@MCPUPDATE` zůstane starý kód (poznáš podle `tools_count`
v `@@MCPHEALTH`, který se nezmění), a je nutný ruční `Restart-Service EUROSOFT-MCP`
z účtu s právy.

Cíl: udělit účtu služby právo **Start+Stop nad vlastní službou**, aby si self-update
restart provedl sám. Vše se spouští na **EC-SERVER2** v PowerShellu **jako správce**.

---

## Krok 1 — Zjisti, pod jakým účtem služba běží (diagnostika)

```powershell
Get-CimInstance Win32_Service -Filter "Name='EUROSOFT-MCP'" |
  Select-Object Name, StartName, State
# alternativně:
sc.exe qc EUROSOFT-MCP            # řádek SERVICE_START_NAME
nssm get EUROSOFT-MCP ObjectName # pokud je služba pod NSSM
```

Podle výsledku (`StartName` / `SERVICE_START_NAME`):

- **`LocalSystem` / `NT AUTHORITY\SYSTEM`** → účet už práva k restartu **má**.
  Příčina selhání pak není v oprávnění → pokračuj sekcí **D (když je to SYSTEM)**.
- **Konkrétní účet** (např. `.\eurosoftsvc`, `NT SERVICE\EUROSOFT-MCP`, doménový
  účet) → chybí mu právo Stop/Start → pokračuj **Krokem 2**.

---

## Krok 2 (DOPORUČENO) — Grant Start+Stop přes SDDL služby

Uděluje účtu služby jen `SERVICE_START` (RP) + `SERVICE_STOP` (WP) +
`SERVICE_QUERY_STATUS` (LC). Nic víc — žádná změna konfigurace, žádné admin právo.

```powershell
$svc  = 'EUROSOFT-MCP'
$acct = 'NT SERVICE\EUROSOFT-MCP'   # << DOSAĎ skutečný účet z Kroku 1

# 1) ZÁLOHA původního deskriptoru (nutné pro případný rollback)
New-Item -ItemType Directory -Force C:\Backup | Out-Null
$orig = ((sc.exe sdshow $svc) | Where-Object { $_ -match 'D:' }) -join ''
$orig | Tee-Object C:\Backup\mcp_sddl_backup.txt

# 2) SID účtu
$sid = (New-Object System.Security.Principal.NTAccount($acct)).
         Translate([System.Security.Principal.SecurityIdentifier]).Value
"SID: $sid"

# 3) Nové ACE (Start+Stop+QueryStatus) vlož na KONEC DACL (před SACL 'S:')
$ace = "(A;;RPWPLC;;;$sid)"
if ($orig -match '^(D:.*?)(S:.*)$') { $dacl=$Matches[1]; $sacl=$Matches[2] }
else { $dacl=$orig; $sacl='' }
$new = $dacl + $ace + $sacl
"Nový SDDL:`n$new"

# 4) APLIKUJ
sc.exe sdset $svc $new

# 5) OVĚŘ (nový ACE s tvým SID musí být vidět)
sc.exe sdshow $svc
```

> **Pozn.:** Pokud `sc.exe sdset` vrátí chybu „(1352) The security account
> manager (SAM) …" nebo „FAILED 87", SDDL je špatně poskládaný — **neaplikuj nic
> dalšího** a obnov ze zálohy (viz Rollback). Nejčastější příčina: ACE se vložil
> až za `S:` (SACL) místo do `D:` (DACL).

---

## Krok 3 — Ověř celou smyčku (bez ručního restartu)

Z běžného kanálu (bridge) pusť:

```
@@MCPHEALTH          # zapiš si tools_count PŘED
```

Udělej drobnou změnu v MCP a spusť `@@MCPUPDATE`, pak znovu:

```
@@MCPHEALTH          # tools_count / git_sha se MUSÍ změnit sám, bez Restart-Service
```

Když se `git_sha` i `tools_count` posunou bez ručního zásahu → **hotovo**,
`@@MCPUPDATE` je bezobslužný.

---

## Rollback (kdyby cokoli zlobilo)

```powershell
$orig = Get-Content C:\Backup\mcp_sddl_backup.txt
sc.exe sdset EUROSOFT-MCP $orig
sc.exe sdshow EUROSOFT-MCP     # ověř návrat k původnímu
```

Grant nic nemaže ani nemění chování služby — jen přidává právo Start/Stop. Rollback
ho čistě odebere.

---

## Alternativa (robustnější, bez zásahu do SDDL) — SYSTEM scheduled task

Pokud nechceš sahat na security descriptor, vytvoř naplánovanou úlohu běžící jako
`SYSTEM`, která dělá stop→copy→start, a nech self-update jen spustit ji:

```powershell
$action  = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument '-NoProfile -ExecutionPolicy Bypass -File C:\eurosoft_mcp\restart_and_sync.ps1'
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName 'EUROSOFT-MCP-SelfUpdate' -Action $action -Principal $principal
```

`restart_and_sync.ps1` (jako SYSTEM): `Stop-Service EUROSOFT-MCP` → `robocopy`
repo→pkg `*.py /MIR? (jen soubory)` → `Start-Service EUROSOFT-MCP`. Self-update pak
místo přímého Stop-Service zavolá `schtasks /run /tn EUROSOFT-MCP-SelfUpdate`.
Tato varianta vyžaduje malou úpravu self-update kódu — **řekni a doplním ji.**

---

## D — Když služba běží jako LocalSystem (a přesto to nejde)

LocalSystem už právo Stop/Start má, takže příčina je jinde. Zkontroluj:

1. **Odpojený PowerShell vůbec neběží** — self-update ho spouští `subprocess`em;
   ověř v logu MCP, jestli se řádek se `Stop-Service` vypsal.
2. **robocopy nezkopíroval `.py`** — chybný zdroj/cíl (repo vs pkg cesty), nebo
   běželo pod jiným CWD. Ověř časové razítko `filesystem_tools.py` v pkg složce
   `C:\eurosoft_mcp\eurosoft_mcp\` po pokusu.
3. **Proces se restartoval, ale kód je pořád starý** — pak se `.py` nepřepsal
   (bod 2), protože samotný restart k načtení stačí.

V tomto případě dej vědět — půjde spíš o opravu self-update skriptu než o oprávnění.

---

*Připravil Claude (ID23), 3. 7. 2026 — aby síť Claudů byla u MCP updatů plně
autonomní a odpadly ruční `Restart-Service`.*
