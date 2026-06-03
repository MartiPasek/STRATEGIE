# STRATEGIE — vize nativní mobilní aplikace (Android-first)

**Stav:** plán / vize (3. 6. 2026). Není v realizaci — mezikrok je CardDAV + PWA.
**Autoři:** Marti + Claude.

---

## Proč

CardDAV + DAVx5 je **chytrý mezikrok** — dá caller-ID (při hovoru jméno klienta)
bez vlastní aplikace. Ale platíme dvěma věcmi:

1. **Křehké nastavení** pro netechnické lidi (instalace DAVx5 + poplatek,
   seskupování podle kategorií, interval synchronizace, VPN volba…).
2. **Neřídíme UX ani push** — telefon si tahá kontakty sám, my do něj
   nepushneme, notifikace jsou cizí appky.

Marti (3. 6. 2026): *„V budoucnu to bude chtít vlastní nativní naši aplikaci,
která bude umět s námi komunikovat. Nejlepší by bylo vyjít z nějaké open-source
a doladit k našim potřebám. Tahle problematika se nás bude týkat víc a víc."*

---

## Doporučený přístup — zabalit stávající PWA přes Capacitor

**Nestavět od nuly.** Naše web UI (chat + ERP + CRM) už je PWA. Capacitor
(Ionic, open-source) z ní udělá nativní Android app a přidá nativní pluginy.
Tím reuse-neme **veškerý dosavadní web** a doplníme jen to, co web neumí.

Open-source základ = **Capacitor** + naše vlastní webová aplikace. Přesně ve
smyslu *„vyjít z open-source a doladit"*.

### Co appka přidá nad web

| Schopnost | Co řeší | Plugin / cesta |
|---|---|---|
| **Kontakty / caller-ID** | jméno klienta při hovoru, **jeden login** (token STRATEGIE), bez DAVx5 | nativní Contacts API + náš sync; inspirace DAVx5 (GPL) pro sync logiku |
| **Push notifikace** | doručí i při zavřené appce (to, co pořád chceme) | FCM (Firebase Cloud Messaging) |
| **Nativní vytáčení / overlay** | klik-volat z CRM, případně overlay při příchozím | Android Call API / overlay |
| **Offline + nativní pocit** | rychlost, instalace z Play | Capacitor app shell |

Chat, ERP, CRM, deploy bridge, auth — **beze změny**, je to naše web UI uvnitř
nativního obalu.

### Alternativy (a proč ne teď)

- **React Native / Flutter od nuly** — víc nativní pocit, ale **přepis celého
  UI** = velký kus práce. Náš web je hotový, škoda ho zahodit.
- **Fork DAVx5** (GPL) — řeší jen kontakty, ne komunikaci s námi (chat/CRM).
  Moc úzké.

---

## Platformy — Android-first

**Rozhodnutí (Marti 3. 6. 2026):** v následujícím roce **jen Android**. Celá
firma je na Androidu. Apple (iOS) se řešit nebude, dokud si ho **nezaplatí
konkrétní zákazník** — pak se přidá (Capacitor umí iOS taky, jen je k tomu
potřeba Apple Developer účet).

Důsledky:
- Vývoj, build a testy jen pro Android → jednodušší, levnější.
- iOS se nechá jako pozdější „dolepení" (stejná code-base, jen build + Apple účet).

---

## Náklady (ověřit aktuální ceny při rozhodnutí)

- **Google Play** — jednorázový registrační poplatek vývojáře (~$25). FCM má
  free tier.
- **Apple Developer** — ~$99/rok. **Odloženo** (až platící zákazník).
- Build pipeline (Android Studio / CI), údržba, podpis appky.

Capacitor cesta je z variant **nejlevnější na úsilí** — nepřepisujeme appku.

---

## Fázování

1. **Teď:** CardDAV + PWA mezikrok (funguje, caller-ID přes DAVx5).
2. **Až bude friction/objem bolet:** Capacitor wrap → Android app v Play s
   nativními kontakty (bez DAVx5) + push.
3. **Později / na vyžádání:** iOS build (Apple účet platí zákazník).

---

## Otevřené otázky (na rozhodnutí, až se to rozjede)

- Caller-ID: sync kontaktů do telefonu (jako DAVx5, ale 1 login) **vs.** vlastní
  overlay při hovoru? (sync = jednodušší, overlay = víc kontroly)
- Push: jen notifikace, nebo i akce (klik → otevři kontakt/CRM)?
- Distribuce: veřejně v Play, nebo interní (firemní) distribuce?
- Kdo to postaví/udržuje (interně vs. externě).

---

*Tento dokument je živý — doplní se, až se appka dostane na řadu.*
