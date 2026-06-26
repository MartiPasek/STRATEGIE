# 📑 Google Play — Permissions Declaration (SMS + Call Log) pro STRATEGIE Mobil

> Připravil Claude (id=28) s Jirkou, 26. 6. 2026. Doplněk k
> `google_play_formulare_pripravene.md` a `google_play_priprava.md`.
>
> **Účel:** texty k vložení do **Permissions Declaration Form** v Play Console
> (objeví se při nahrání AAB, který žádá SMS / Call Log oprávnění) + scénář
> video dema, které Google u těchto oprávnění **vyžaduje**.
>
> **Rozhodnutí Jirka 26. 6. 2026:** SMS i Call Log chceme zachovat i ve **veřejné**
> Play verzi (jsou to funkce, které firma i budoucí zákazníci ocení). Call Log
> deklarujeme jako součást **CRM modulu STRATEGIE** (automatizace procesů v CRM).

---

## 0. Co Google Play povoluje (ověřeno 26. 6. 2026)

Zdroj: [Use of SMS or Call Log permission groups](https://support.google.com/googleplay/android-developer/answer/10208820?hl=en).
SMS/Call Log smí veřejná appka používat **jen pro povolený účel** + vyplnit
Permissions Declaration + **dodat video demo**; Google schvaluje ručně.

| Funkce STRATEGIE | Oprávnění | Povolený účel Google | Stav |
|---|---|---|---|
| SMS s firemními kontakty (odeslání, archivace do CRM) | `SEND_SMS`, `READ_SMS`, `RECEIVE_SMS` | **Enterprise CRM and archiving** | ✅ Deklarovat |
| Historie hovorů → CRM automatizace | `READ_CALL_LOG` | **Enterprise device management** + Caller ID | ⚠️ Deklarovat (může chtít doplnit) |
| Rozpoznání volajícího (caller-ID) | `READ_CONTACTS` | — (běžné oprávnění, bez deklarace) | ✅ |
| Self-update (stažení APK) | `REQUEST_INSTALL_PACKAGES` | — Play to ZAKAZUJE | ❌ Z veřejné verze ven |
| Přeposílání **ověřovacích** SMS (token „STG-") | `RECEIVE_SMS` | „Account verification via SMS" = **zakázáno** | ❌ Jen interní sideload, ne veřejně |

> **Důležité:** „account verification via SMS" je výslovně zakázaný účel.
> Proto se ve **veřejné** verzi NESMÍ tvářit, že SMS bránu používáme na ověřování.
> Příjem/odesílání SMS deklarujeme čistě jako **firemní komunikaci a archivaci (CRM)**.
> Ověřovací SMS brána zůstává jen v **interní sideload** verzi pro EUROSOFT.

---

## 1. Declaration — SMS permissions

**Vybraný core use case (zaškrtnout):** *Enterprise CRM and archiving*

**Justification text (vložit do pole „Describe how your app uses..."):**

```
STRATEGIE is a business (B2B) platform that companies deploy for their own
employees. The SMS permissions are core functionality of the built-in CRM
module: employees send and receive SMS messages with the company's business
contacts (customers and suppliers) directly from the app, and these messages
are archived against the corresponding customer record in the company's CRM.

Specifically:
- SEND_SMS: an employee sends an SMS to a business contact from inside the
  customer's CRM card (e.g. order confirmation, appointment reminder).
- READ_SMS / RECEIVE_SMS: incoming and outgoing SMS with business contacts are
  logged and archived into the CRM history of that contact, so the full
  communication timeline with the customer is available to the company.

Messages are processed only for contacts that exist in the company's own
business address book. All data is stored on the company's own STRATEGIE server
(self-hosted / private tenant), is transmitted over HTTPS, is never sold or
shared with third parties, and is never used for advertising. The app requires
a company account to function. SMS is NOT used for account verification.
```

> Pozn.: pokud Google nabízí přesnější dílčí volby (např. „archiving business
> communications"), vyber tu nejbližší k CRM/archivaci.

---

## 2. Declaration — Call Log permission (`READ_CALL_LOG`)

**Vybraný core use case (zaškrtnout nejbližší):** *Enterprise device management*
(a pokud nabízí i *Caller ID / spam*, zaškrtnout i to).

**Justification text (vložit — postaveno na CRM automatizaci, dle zadání Jirky):**

```
STRATEGIE is a business (B2B) platform deployed by companies to their employees.
READ_CALL_LOG is core functionality of the STRATEGIE CRM module, which uses the
call history to AUTOMATE customer-relationship workflows:

1. When an employee has a phone call with a business contact (a customer or
   supplier already stored in the company address book), STRATEGIE reads that
   call entry (number, timestamp, direction, duration) and links it to the
   customer's CRM record, building a complete, automatic communication timeline
   for the company.

2. Based on the call log, the CRM automatically triggers business actions:
   logging the call to the customer's history, creating follow-up tasks for
   missed customer calls, and updating the activity record of the deal — so the
   company's sales/support processes run without manual data entry.

The call log is read ONLY for numbers that match the company's own business
contacts (filtered by the company's contact prefixes); private/personal calls
are ignored and never leave the device. All data is stored on the company's own
STRATEGIE server (private tenant), transmitted over HTTPS, never sold or shared
with third parties, and never used for advertising. The feature exists purely to
automate the company's internal CRM and customer-service processes.
```

**Co zdůraznit recenzentovi (proč to potřebujeme):**
- Je to **enterprise B2B** nástroj — firma ho nasazuje vlastním zaměstnancům.
- Call log = **vstup pro automatizaci CRM** (ne marketing, ne profilování).
- Čte se **jen u firemních kontaktů**, soukromé hovory se ignorují.
- Data jdou na **vlastní server firmy**, neprodávají se, žádná reklama.

> ⚠️ **Realita:** Call Log nemá tak čistý „enterprise CRM" účel jako SMS. Google
> může požádat o doplnění nebo odmítnout. Proto máme připravený **fallback**
> (bod 4) — appka i bez `READ_CALL_LOG` zůstane plně funkční (caller-ID přes
> kontakty), jen historie hovorů→CRM bude v interní verzi.

---

## 3. Video demo (Google ho u SMS/Call Log vyžaduje)

Krátké video (1–2 min, nahrané na YouTube jako „unlisted", odkaz do formuláře),
které ukáže, že oprávnění jsou **core funkce**:

1. Otevři appku, přihlas se firemním účtem (CRM modul).
2. Otevři kartu zákazníka v CRM.
3. **SMS:** pošli SMS zákazníkovi z karty → ukaž, že se SMS objeví v historii
   komunikace u toho zákazníka.
4. **Call Log:** ukaž seznam posledních hovorů s firemními kontakty v appce →
   ukaž, jak se hovor automaticky propíše do historie zákazníka v CRM a jak
   vznikne navazující úkol (automatizace).
5. (Volitelně) ukaž obrazovku oprávnění, kde appka o přístup žádá s vysvětlením.

> Demo dělej na účtu **s reálnými daty** (ne prázdné demo) — recenzent musí
> vidět skutečnou funkci. Mluvený nebo titulkovaný komentář anglicky pomůže.

---

## 4. Fallback, kdyby Google Call Log odmítl

Aby nás zamítnutí Call Logu **nezablokovalo** na produkci:
- Veřejnou Play verzi lze vydat **bez `READ_CALL_LOG`** (build flavor / přepínač).
- Caller-ID dál funguje přes `READ_CONTACTS` (povoleno bez deklarace).
- Historie hovorů → CRM zůstane v **interní sideload** verzi pro EUROSOFT.
- SMS (Enterprise CRM) deklarujeme zvlášť — to projde nezávisle na Call Logu.

---

## 5. Build — co musí Claude (id=23) připravit před nahráním AAB

> Build AAB dělá Claude id=23 přes build bridge. Tohle je checklist změn pro
> **veřejnou Play variantu** (interní sideload verze zůstává beze změny).

- [ ] **Vypnout self-update:** odstranit `REQUEST_INSTALL_PACKAGES` z manifestu,
      `InstallActivity` + FileProvider pro APK + JS most na stažení/instalaci APK.
      Důvod: WebView obal — web změny se propíšou samy; nativní změny = nová Play
      verze (Play řeší update sám). Toto Play u veřejné verze **vyžaduje**.
- [ ] **Vypnout přeposílání ověřovacích SMS** (SmsReceiver větev „STG-") ve
      veřejné verzi — „account verification via SMS" je zakázáno. SMS pro CRM
      (firemní kontakty) zůstává.
- [ ] **Ponechat** `SEND_SMS`/`READ_SMS`/`RECEIVE_SMS` (deklarace = Enterprise CRM),
      `READ_CALL_LOG` (deklarace = CRM automatizace), `READ_CONTACTS`, `RECORD_AUDIO`,
      notifikace.
- [ ] Připravit jako **build flavor** (`play` vs `internal`), ať umíme rychle
      vydat verzi bez `READ_CALL_LOG`, kdyby Google odmítl (bod 4).

---

*Tento dokument je příprava textů a podkladů. Nic nenasazuje. Deklarace se
vyplňuje v Play Console při nahrání AAB; video demo se přikládá odkazem.*
