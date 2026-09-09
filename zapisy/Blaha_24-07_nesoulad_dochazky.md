# Bláha 24. 7. 2026 — proč se docházka neshoduje (zápis)

**Krátce a polopaticky:** dvě místa v systému čtou **dvě různé tabulky**, a ty se dnes u Bláhy rozešly.

| Kde | Co to čte | Začátek | Celkem |
|---|---|---|---|
| **Mobil + Docházka new** | zakázkové časy (rozpad po zakázkách) | 05:49 | **~4,3 h** — sedí s tím, co Bláha vidí na mobilu (4,29 h) |
| **Opravy docházky** | docházková píchnutí (příchod/přestávka/zakázka) | **04:57** | **~6 h** |

**Rozdíly u „Opravy docházky":**
- začíná **04:57** (o ~52 min dřív než zakázky),
- ráno je **slité na jednu zakázku** (VR10700, 3,20 h), zatímco v zakázkách je to rozdělené (VR10699, VR10694, VR10700),
- navíc je tam blok **Režie 09:17–10:34 (1,29 h)**, který v zakázkách vůbec není.

→ „Opravy docházky" ukazují o **~1,7 h víc** a jiný rozpad než realita ze zakázek a než co vidí Bláha na mobilu.

**Důležité:**
- Není to chyba nové „Správy docházky".
- Je to **nesoulad mezi docházkovým a zakázkovým systémem** (jak se plní `att_entry` vs `vyroba_work`).
- Protože **docházka jde do mezd**, je to potřeba dořešit — ne kosmetika. Stejný jev je i u Dvořákové.

**Co dál:** najít v kódu, jak se plní ty dvě tabulky a kde vzniká rozdíl (časný začátek + blok Režie navíc). U mezd nic neopravovat naslepo.

---

### Obrázky (přílohy)

*(screenshoty přetáhni na označená místa)*

**[Obrázek 1 — mobil Bláhy]** co vidí on sám: 24. 7. celkem 4,29 h, zakázky VR10694 / VR10699 / VR10700…

**[Obrázek 2 — Opravy docházky]** začátek 04:57, blok Režie 09:17–10:34 (1,29 h).

**[Obrázek 3 — Docházka new]** začátek 05:49, práce rozdělená po zakázkách (VR10694 0,97 h, VR10700 0,86 h…).
