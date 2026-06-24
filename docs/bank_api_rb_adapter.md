# RB Premium API — adaptér (konkrétní spec z developer portálu, 24.6.2026)

Zdroj: https://developers.rb.cz/premium/ (Swagger Production v1.1.20240910). Host `api.rb.cz`,
schéma https, basePath `/`. První provider `RB_PREMIUM_API` v `tenant.bank_provider`.

## Autentizace (každé volání)
- **`X-IBM-Client-Id`** (header, povinné) — ClientID z registrace appky na portálu.
- **mTLS klientský certifikát** (.p12 / PKCS#12 + heslo) — pro VŠE kromě FX rates.
  Cert se generuje v Internet Bankingu (návod Řeřicha) per účet + per operace (http metoda).
  → trezor (`bank_connection.vault_ref`), dešifrování ephemeral pro konkrétní call (Marti-AI).
- **`X-Request-Id`** (header, povinné) — unikátní id requestu, audit. Pattern `[a-zA-Z0-9\-_:]{1,60}`.
- **`PSU-IP-Address`** (header, volitelné) — IP koncového uživatele.

### Cert lifecycle (HLÍDAT!)
Platnost ~5 let, ale **každý rok se certifikát automaticky zablokuje** → uživatel ho musí
odblokovat v IB (lze předem prodloužit). Adaptér: detekovat `401 INVALID_REQUEST` /
„certificate in invalid state" → notifikace uživateli (PWA/mail) S PŘEDSTIHEM. Bez odblokování
API přestane číst.

## Endpointy — Fáze 1 (READ)
| Operace | Metoda + path | Pozn. |
|---|---|---|
| Seznam účtů | `GET /rbcz/premium/api/accounts?page&size` | accountId, accountNumber(+prefix), iban, bankCode, mainCurrency, accountTypeId; stránkováno |
| Zůstatek | `GET /rbcz/premium/api/accounts/{accountNumber}/balance` | typy CLAV (disponibilní), CLBD (účetní), CLAB (akt. bez limitu), BLCK (blokace) |
| Transakce | `GET /rbcz/premium/api/accounts/{accountNumber}/{currencyCode}/transactions?from&to&page` | **max 90 dní zpět**; stránky (`lastPage` flag); `from`/`to` ISO date(-time) |
| Seznam výpisů | `POST /rbcz/premium/api/accounts/statements` | body: accountNumber, currency, statementLine MAIN/ADDITIONAL/MT940, dateFrom/To |
| Stažení výpisu | `POST /rbcz/premium/api/accounts/statements/download` | body: accountNumber, statementId, statementFormat pdf/xml/MT940 → binární; `Accept-Language cs/en` |
| FX kurzy | `GET /rbcz/premium/api/fxrates[/{currencyCode}]` | **bez certifikátu**; lze použít pro `ucet_kurz` validaci |

## Endpointy — Fáze 2 (PLATBY, write) — přesně model „AI navrhuje, člověk schvaluje"
| Operace | Metoda + path | Pozn. |
|---|---|---|
| Import dávky | `POST /rbcz/premium/api/payments/batches` | header `Batch-Import-Format` (SEPA-XML/DOM-XML/ABO-KPC/CFD/CFU/CFA/GEMINI-*); tělo = obsah dávky |
| Stav dávky | `GET /rbcz/premium/api/payments/batches/{batchFileId}` | status DRAFT/FOR_SIGN/VERIFIED/PASSED… |

**🔑 Klíčové:** import platby ji NEPROVEDE — jen ji **nahraje do IB**, kde ji uživatel musí
**autorizovat/podepsat** (disponentská práva + podpisy). To je 1:1 model Marti-AI:
`bank_payment_order` (navrženo) → import batch (FOR_SIGN) → **člověk podepíše v IB** → PASSED.
Naše appka platbu NIKDY neodešle sama; jen připraví dávku + sleduje stav.

## Mapování transakce → `tenant.bank_transaction_raw`
| RB pole | staging sloupec |
|---|---|
| `entryReference` | `ext_id` (dedup, UNIQUE per account) |
| `amount.value` / `amount.currency` | `castka` / `mena` |
| `creditDebitIndication` (DBIT/CRDT) | `smer` (out/in) |
| `bookingDate` | `datum` |
| counterParty `account.iban` / `accountNumber` | `protiucet` |
| `creditorReferenceInformation.variable/constant/specific` | `vs` / `ks` / `ss` |
| `remittanceInformation.unstructured` / `originatorMessage` | `zprava` |
| celý objekt transakce | `raw` (jsonb) |

Tok: adaptér `get_transactions` → normalizace → upsert `bank_transaction_raw` (ON CONFLICT
account_id+ext_id) → párovací engine → `ucetni_denik` (staging doktrína Marti-AI).

## Rate limiting
10 req/s + 5000/den per client; Download Statement 5/s + 1500/den. Ošetřit **HTTP 429**
(retry s backoff). Hlídat headery `X-RateLimit-Remaining-Second/Day`.

## Sandbox (test PŘED produkčním certem)
Sandbox prostředí + **testovací cert** (heslo `Test12345678`) na portálu → adaptér jde
odladit (read operace) bez čekání na Martiho produkční cert. Potřeba: registrace appky
(ClientID) na portálu. Doc: https://developers.rb.cz/premium/documentation/02rbczpremiumapi_sandbox

## Adaptér — implementační poznámky
- Jeden modul `rb_premium_adapter` implementující rozhraní providera: `list_accounts`,
  `get_balances`, `get_transactions(acc,ccy,from,to)`, `list_statements`, `download_statement`,
  `(F2) import_payment_batch`, `get_batch_status`.
- mTLS: `requests` s `cert=(p12→pem)` nebo `httpx` + `ssl` kontext; .p12 dešifrovat ephemeral
  z trezoru (nikdy na disk natrvalo / do logu).
- Každý call → `bank_api_log` (uroven=batch pro čtení, event pro platby).
- Normalizovaný výstup = stejná struktura napříč providery (univerzalita).

## Co potřebujeme od/s Martim (a od Řeřichy)
1. **Certifikát** v IB (read scopes: historie/zůstatky/výpisy) → heslo do trezoru. (Marti)
2. **Registrace appky na portálu → ClientID** (`X-IBM-Client-Id`). (portál, Marti/my)
3. Potvrzení od Řeřichy (dokumentace už máme z portálu — stačí ClientID + cert).
4. Sandbox ClientID + test cert pro odladění.

— Claude (id=23), 24.6.2026 — z živé Swagger spec RB Premium API (zatímco Marti generuje cert)
