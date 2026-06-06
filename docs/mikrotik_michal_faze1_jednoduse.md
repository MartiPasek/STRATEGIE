# Mikrotik — krok za krokem (fáze 1: vidět zařízení na síti)

**Pro:** Michal
**Co od tebe potřebujeme:** read-only (jen ke čtení) přístup k routeru, abychom ve
STRATEGII viděli, **která zařízení jsou na firemní síti** (telefony, PC, tiskárny…).
Router to už ví — my si to chceme jen číst. **Nic se nemění, nic se nemaže.**

Zabere to ~5 minut přes **Winbox** (to okno, co používáš na správu routeru).
Router je `192.168.30.1`.

---

## Krok 1 — Zjisti verzi routeru
Ve Winboxu vlevo klikni na **System → Resources**.
V okně najdi řádek **Version** (např. `6.49.x` nebo `7.15.x`).
👉 **Napiš nám jen to číslo** (6 nebo 7). Podle toho jsou další kroky.

---

## Krok 2 — Zapni čtecí službu
Vlevo klikni na **IP → Services**. Uvidíš seznam služeb.

- **Když je verze 7:** najdi řádek **`www-ssl`** → klikni na něj → nahoře dej
  **Enable** (zaškrtni / odškrtni „Disabled"). (Je to port 443.)
- **Když je verze 6:** najdi řádek **`api`** → klikni na něj → nahoře **Enable**.
  (Je to port 8728.)

> Stačí zapnout tu jednu službu. Ostatní nech, jak jsou.

---

## Krok 3 — Vytvoř čtecího uživatele
Vlevo klikni na **System → Users**. Nahoře záložka **Users** → klikni na **„+"**
(přidat). Vyplň:

- **Name:** `stratread`
- **Group:** `read`  ← důležité: tahle skupina **umí jen číst**, nemůže nic změnit
- **Password:** vymysli silné heslo
- **Allowed Address:** `192.168.30.10/32`  ← povolí přihlášení jen z našeho serveru
- Klikni **OK**.

👉 To **heslo nám pošli zvlášť** (ne přes chat — SMS, nebo nadiktuj Martimu).

---

## Krok 4 — Firewall (jen pokud router blokuje vstup)
Většinou je potřeba routeru říct, že náš server smí na tu službu.

Vlevo **IP → Firewall** → záložka **Filter Rules**.
Jestli tam máš pravidlo, které na konci **dropuje** vstup (chain `input`, action
`drop`), přidej **NAD něj** nové pravidlo (**„+"**):

- Záložka **General:**
  - **Chain:** `input`
  - **Protocol:** `tcp`
  - **Dst. Port:** `443` (verze 7) / `8728` (verze 6)
  - **Src. Address:** `192.168.30.10`
- Záložka **Action:** `accept`
- **OK**, a pravidlo **přetáhni myší nahoru** nad to drop pravidlo.

> **Nejsi si jistý, jestli tam nějaký drop je?** Udělej screenshot okna
> **IP → Firewall → Filter Rules** a pošli nám ho — řekneme ti, jestli krok 4
> vůbec potřebuješ.

---

## Hotovo
Pošli nám prosím:
1. **verzi** (6 / 7),
2. **heslo** uživatele `stratread` (zvlášť, ne chatem),
3. že je to nastavené.

My si pak ověříme spojení a spustíme čtení. Od té chvíle STRATEGIE uvidí, kdo/co
je na síti — bez čehokoliv nainstalovaného na ta zařízení.

---

### Poznámka
**Tohle je fáze 1** — jen identifikace běžících zařízení na síti.
**Fáze 2** (později) bude **sledování a bezpečnostní diagnostika** routeru — tu
probereme zvlášť, až tohle poběží.
