# SMS Gateway — nastavení

STRATEGIE posílá SMS přes **Android telefon se SIM kartou** jako SMS bránu.
Aplikace zapisuje pending SMS do `sms_outbox`, telefon si je periodicky
stahuje a posílá je přes mobilní síť.

Výhody: vlastní firemní číslo, předvídatelné náklady (pouze tarif SIMky),
plná kontrola, žádný třetí provider.

## Architektura

```
STRATEGIE ──── sms_outbox (data_db) ←── HTTPS poll ──── Android telefon
                    ↑                                         │
                    │                                         │
          queue_sms() zapisuje                  posílá SMS přes GSM síť
                                                              │
                               confirm sent/failed ←──────────┘
```

Telefon **iniciuje** komunikaci (pull), server nikdy telefon nekontaktuje.
Díky tomu telefon nepotřebuje veřejnou IP ani port forwarding, může být
za NATem, na WiFi nebo mobilních datech, kdekoli.

## 1. Příprava serveru

### 1.1 Migrace databáze

```powershell
cd D:\Projekty\STRATEGIE
poetry run alembic -c alembic_data.ini upgrade head
```

Vytvoří tabulku `sms_outbox`.

### 1.2 Vygeneruj gateway key

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Dostaneš např. `7k3hX8_p-4VqR0YcE2bFa1T9NmU6WjLhS5gA-OdK8Pw`.
Zkopíruj si ho — budeš ho potřebovat 2x (server i telefon).

### 1.3 `.env` konfigurace

Přidej (nebo uprav) tyto řádky v `D:\Projekty\STRATEGIE\.env`:

```
SMS_ENABLED=true
SMS_PROVIDER=android_gateway
SMS_GATEWAY_KEY=7k3hX8_p-4VqR0YcE2bFa1T9NmU6WjLhS5gA-OdK8Pw
SMS_FROM_NUMBER=+420777180511
SMS_RATE_LIMIT_PER_USER_PER_HOUR=5
```

(Nahraď `SMS_GATEWAY_KEY` hodnotou z kroku 1.2.)

### 1.4 Restart služby

```powershell
nssm restart STRATEGIE-API
```

### 1.5 Test endpointu

```powershell
# Pres curl / Invoke-RestMethod -- vrati 401 pri spatnem klici, 200 s prazdnym seznamem pri spravnem
Invoke-RestMethod `
  -Uri "https://app.strategie-system.com/api/v1/sms/gateway/outbox" `
  -Headers @{ "X-Gateway-Key" = "<tvuj-klic>" }
```

Očekávaný response: `{"items": [], "count": 0}`.

## 2. Příprava telefonu

### 2.1 Požadavky

- Android 7.0+ (Nougat a vyšší)
- SIMka s kreditem / tarifem pokrývajícím SMS
- Stabilní WiFi nebo mobilní data
- Nabíječka (telefon musí být trvale zapnutý, s FG service)

### 2.2 Instalace aplikace

Doporučená aplikace: **SMS Gateway for Android** (capcom6/android-sms-gateway)

- F-Droid: https://f-droid.org/en/packages/me.capcom.smsgateway/
- Google Play (pokud používáš): hledej „SMS Gateway capcom6"
- GitHub (APK + zdroj): https://github.com/capcom6/android-sms-gateway

Nainstaluj a otevři.

### 2.3 Povolení oprávnění

Aplikace při startu požádá o:
- **Permission: Send SMS** — povol
- **Permission: Read SMS** (pro delivery reports) — povol
- **Battery optimization: Don't optimize** — povol (jinak Android zabije service)
- **Auto-start at boot** — povol (v nastaveních telefonu, výrobce-specific)

### 2.4 Režim „Private server"

V aplikaci přepni na režim, kde telefon **pulluje** ze serveru (ne relayem
capcom6 cloudu):

1. Settings → **Mode** → zvol variantu kdy telefon je **"Worker"** / **"Private"**
   (název se liší podle verze appky — klíčové je, že telefon volá HTTP API)
2. Zadej:
   - **Server URL**: `https://app.strategie-system.com/api/v1/sms/gateway`
   - **Auth / API key** (header `X-Gateway-Key`): vlož hodnotu z kroku 1.2
   - **Poll interval**: 15-30 sekund
3. Pokud aplikace používá vlastní endpointové pojmenování, mapping je:
   - GET outbox          → `GET  /outbox`
   - POST confirm sent   → `POST /outbox/{id}/sent`
   - POST report failed  → `POST /outbox/{id}/failed`

> Pokud capcom6 mode v tvé verzi neumí nativně naše API tvar, máme dvě
> volby: (a) napsat malý adapter endpoint, který mluví jejich jazykem,
> (b) přejít na Tasker / HTTP Request Shortcuts s vlastním skriptem.
> Vyřešíme při integraci.

### 2.5 Test odeslání z telefonu

1. V STRATEGIE chatu řekni: *„Pošli SMS na +420777180511 text TEST"*
   (samotný AI tool `send_sms` přijde v Fázi 2 — zatím testuj přes Python
   shell: `from modules.notifications.application.sms_service import queue_sms;
   queue_sms("777180511", "test", purpose="system")`)
2. Na telefonu by se do 30 sekund objevila SMS v odchozích.
3. V DB: `SELECT * FROM sms_outbox ORDER BY id DESC LIMIT 5;` → status=`sent`.

## 3. Provoz

### Kontrola stavu

```sql
-- Kolik je v outboxu pendingu (mělo by být skoro 0, pokud telefon frčí)
SELECT status, COUNT(*) FROM sms_outbox GROUP BY status;

-- Posledních 10 SMS
SELECT id, to_phone, status, created_at, sent_at, last_error
FROM sms_outbox ORDER BY id DESC LIMIT 10;
```

### Rate limit pro usery

`SMS_RATE_LIMIT_PER_USER_PER_HOUR=5` = jeden user může poslat max 5 SMS
za hodinu přes AI tool. Vyšší limit? Uprav v `.env` + restart.

### Rozpoznání problémů

**Outbox plný pendingů a roste:**
- Telefon nepulluje — zkontroluj, jestli běží na telefonu foreground service
- Reboot telefonu, znovu pustit aplikaci
- Zkontroluj `last_error` v `sms_outbox` u failed záznamů

**Telefon posílá, ale SMS nedorazí:**
- SIM bez kreditu / konec tarifu
- Operátor detekuje „spam" (T-Mobile / O2 mají nedokumentovaný limit
  ~100 SMS/den z běžné SIM). Na 30 SMS/den to nevadí.

**401 Unauthorized v API:**
- Nesedí `SMS_GATEWAY_KEY` mezi serverem a telefonem
- Klič má < 32 znaků (server rejectuje i platný, pokud je slabý)

## 4. Migrace na SMSEagle (budoucnost)

Až objemy narostou (~100+ SMS/den a víc), nebo budeš chtít redundanci
a profi HW, přepnutí je lineární:

1. Koupit SMSEagle (NXS-9700, ~22 tis. Kč)
2. Portovat SIMku do krabičky (nebo dát novou)
3. Napsat `SmsEagleProvider(SmsProvider)` v `sms_service.py`
   (HTTPS POST na jejich `/api/json/sms/send`)
4. Změnit `.env`: `SMS_PROVIDER=smseagle` + `SMSEAGLE_URL` + `SMSEAGLE_TOKEN`
5. Restart
6. Android telefon vypnout

Outbox i AI tool zůstávají beze změny — je to jen výměna transport vrstvy.
