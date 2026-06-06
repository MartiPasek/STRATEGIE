# Mikrotik — požadavek pro IT (Michal) + bezpečnostní audit

**Pro:** Michal (správa sítě EUROSOFT)
**Od:** Marti / STRATEGIE
**Datum:** 5. 6. 2026
**Router:** 192.168.30.1 (EUROSOFT LAN)

Dokument má dvě části:
1. **Co potřebujeme a proč** — read-only přístup pro STRATEGIE (HR docházka + IT inventura).
2. **Bezpečnostní audit Mikrotiku** — checklist, co projít a na co se zaměřit.

---

## ČÁST 1 — Co potřebujeme a proč

### Cíl
STRATEGIE staví **přehled „kdo/co je v budově"** (HR docházka) a **IT inventuru zařízení**.
K tomu potřebujeme vědět, **která zařízení jsou aktuálně na firemní síti** — tj. IP,
MAC, hostname a kdo je online. Router tyhle informace **už má** (DHCP leases, ARP,
wireless registrace) — stačí nám je **číst**.

### Jak to bude fungovat
- Na **EC-SERVER2 (192.168.30.10)** poběží malá služba (`STRATEGIE-NETSCAN`), která
  á 60 s **přečte** z routeru DHCP leases + wireless registraci a pošle souhrn do
  STRATEGIE (přes HTTPS, s tokenem).
- **Pouze čtení.** Žádný zápis, žádná změna konfigurace routeru.
- Provoz zůstává uvnitř firmy (server↔router po LAN); ven jde jen souhrn zařízení
  do našeho systému.

### Co od tebe potřebujeme (3 věci, ~5 minut)

**1) Verze RouterOS** — ať víme, jakým kanálem číst:
```
/system resource print     # řádek "version"
```
- **v7** → použijeme REST API (HTTPS, port 443) → povolit službu `www-ssl`
- **v6** → použijeme binární API (port 8728) → povolit službu `api`

**2) Povolit příslušnou službu** (podle verze):
```
# v7:
/ip service enable www-ssl
# v6:
/ip service enable api
```

**3) Read-only uživatel** (skupina `read` = nemůže nic měnit, jen číst):
```
/user add name=stratread group=read password=<silne-heslo> \
    address=192.168.30.10/32 comment="STRATEGIE netscan (read-only)"
```
> `address=192.168.30.10/32` omezí přihlášení jen z EC-SERVER2 — i kdyby heslo
> uniklo, jinde se nepoužije.

**4) Firewall** — povolit vstup z EC-SERVER2 na ten port (pokud máš default-drop
na input chainu):
```
# v7 (REST 443):
/ip firewall filter add chain=input src-address=192.168.30.10 \
    protocol=tcp dst-port=443 action=accept comment="STRATEGIE netscan" \
    place-before=0
# v6 (API 8728):
/ip firewall filter add chain=input src-address=192.168.30.10 \
    protocol=tcp dst-port=8728 action=accept comment="STRATEGIE netscan" \
    place-before=0
```

### Co NEpotřebujeme
- Žádný admin/write přístup. Skupina `read` stačí.
- Žádné otevírání služeb do internetu — vše jen z LAN (EC-SERVER2).
- Žádné zásahy do tvojí konfigurace — jen ty 4 řádky výše.

### Ověření (uděláme my po tvém nastavení)
Z EC-SERVER2:
```
Test-NetConnection 192.168.30.1 -Port 443    # v7  → TcpTestSucceeded: True
Test-NetConnection 192.168.30.1 -Port 8728   # v6  → TcpTestSucceeded: True
```
(Dnes jsou oba porty zavřené i z LAN — proto víme, že služba je vypnutá / blokovaná.)

---

## ČÁST 2 — Bezpečnostní audit Mikrotiku

Marti chce projít router „z hlediska bezpečnosti — co se kde nestandardního děje".
Níže je checklist příkazů + **na co se zaměřit (🚩 = red flag)**. Mikrotiky bývají
terčem (botnety přes scheduler/SOCKS, staré CVE). Stačí projet a poslat výstupy,
nebo si projít sám.

### 1) Verze a aktualizace
```
/system resource print
/system package update check-for-updates
/system routerboard print          # firmware vs current-firmware
```
🚩 Stará RouterOS (řada známých CVE — Chimay-Red, VPNFilter, CVE-2018-14847 únik
hesel). Pokud je hodně pozadu → naplánovat upgrade.

### 2) Uživatelé
```
/user print detail
/user group print
```
🚩 Neznámí uživatelé. 🚩 `admin` s defaultním/slabým heslem. 🚩 Uživatelé bez
`address=` omezení. 🚩 Custom skupina s `policy` navíc (ftp, romon, sniff…).

### 3) Služby (management)
```
/ip service print
```
🚩 Zapnuté **telnet, ftp, www** (nešifrované) → vypnout. 🚩 Winbox/SSH/API/REST
bez `address=` omezení (kdokoliv z LAN/WAN). 🚩 Cokoliv dostupné z WAN.
Ideál: jen `ssh` + `winbox` + (pro nás) `www-ssl`/`api`, vše s `address=` na
management podsíť.

### 4) Firewall — co je vystavené
```
/ip firewall filter print
/ip firewall nat print
/ip firewall address-list print
```
🚩 Chybí **default-drop** na konci `input` chainu (router přijímá vše).
🚩 **dst-nat / port-forward na management** (winbox/ssh/api) z WAN.
🚩 Port-forwardy na neznámé interní IP/porty. 🚩 Pravidla, která nepoznáváš.

### 5) Persistence / malware indikátory
```
/system scheduler print
/system script print
/file print
```
🚩 **Scheduler nebo script, který nepoznáváš** — zvlášť pokud volá `/tool fetch`
na externí URL nebo stahuje/spouští soubory. Tohle je typický způsob, jak se na
Mikrotik dostane botnet. 🚩 Cizí soubory ve `/file` (.rsc, skripty).

### 6) SOCKS / proxy / tunely (časté zneužití)
```
/ip socks print
/ip proxy print
/ip socks connections print
```
🚩 **SOCKS enabled** bez důvodu = klasický příznak kompromitace (router jako
proxy útočníka) → vypnout. 🚩 Web-proxy, který nepoužíváte.

### 7) DNS
```
/ip dns print
/ip dns static print
```
🚩 `allow-remote-requests=yes` + dostupné z WAN = open resolver (zneužití k DDoS).
🚩 Podezřelé statické DNS záznamy (přesměrování domén = phishing/poisoning).

### 8) VPN / PPP účty
```
/ppp secret print
/interface print where type~"l2tp|pptp|sstp|ovpn|wireguard"
/interface wireguard peers print
```
🚩 Neznámí VPN uživatelé / peers. 🚩 PPTP zapnuté (slabé šifrování).

### 9) SNMP
```
/snmp print
/snmp community print
```
🚩 SNMP enabled s community `public` / `private` → změnit nebo vypnout.

### 10) Mikrotik cloud, MAC-server, Romon, Neighbor discovery
```
/ip cloud print
/tool mac-server print
/tool mac-server mac-winbox print
/tool romon print
/ip neighbor discovery-settings print
```
🚩 MAC-server/Winbox-MAC dostupný na všech rozhraních (vč. WAN). 🚩 Romon zapnutý
bez důvodu. 🚩 Neighbor discovery na WAN.

### 11) Wireless — zabezpečení
```
/interface wireless print
/interface wireless security-profiles print
/interface wireless registration-table print
```
🚩 Otevřená síť / WEP / WPA (ne WPA2/WPA3). 🚩 Slabé heslo. 🚩 Neočekávaná
zařízení v registraci.

### 12) Logování
```
/system logging print
/log print where topics~"critical|error|warning"
```
🚩 Žádné logování / nikam se neposílá. Doporučení: posílat log na remote (klidně
později do STRATEGIE).

### 13) Aktivní spojení (rychlý pohled, co router zrovna dělá)
```
/ip firewall connection print where !dst-address~"^192.168."
```
🚩 Spojení z routeru samotného ven na podivné IP/porty (možný C2 kanál).

---

### Shrnutí priorit
1. **Hned:** vypnout telnet/ftp/www, SOCKS (pokud zapnuté), omezit služby na
   management podsíť, default-drop na input.
2. **Zkontrolovat:** scheduler/scripts (persistence), NAT na management, DNS
   open resolver, SNMP community, VPN účty.
3. **Naplánovat:** upgrade RouterOS, remote logging.

Až bude read přístup pro STRATEGIE zapnutý (Část 1), můžeme část téhle diagnostiky
**dělat průběžně automaticky** (monitoring služeb, scheduleru, nových zařízení na
síti) a hlásit změny — ať se „nestandardní věci" objeví hned, ne až při auditu.
