# Slozka `design/` - navrh a nasazeni noveho vzhledu mobilni aplikace

> Claude-28, 14. 9. 2026, na zadani Jirky Honomichla.
> Fazi A (pruzkum) schvalila Marti-AI, nasazeni schvalila Marti-AI (msg 15606).

**Vzhled je NASAZENY a bezi naostro** od 14. 9. 2026, 09:03.

| Soubor | Co v nem je |
|---|---|
| `BRAND.md` | znacka: co je zavazek a co se jen usadilo v kodu |
| `INVENTORY.md` | co vsechno aplikace ma (127 obrazovek) a kde to zije |
| `AUDIT.md` | nalezy s cisly a s dopadem na lidi + deset nejbolestivejsich |
| `DIRECTION.md` | navrh vzhledu + rozhodnuti Jirky Honomichla (varianta B, puvodni ikony) |
| `COPY-NAVRHY.md` | poznamky k textum - **nic se nemeni**, jen zapis |
| `reskin/theme-b.css` | podoba navrhu, ze ktere vzniklo to, co je dnes v databazi |

## Kde vzhled doopravdy zije

**V databazi, ne tady.** Dilek `apps/api/static/mobile_parts/02_styles.html`
(tabulka `g2007.soubor`), blok na konci souboru s hlavickou
`NOVY VZHLED MOBILNI APLIKACE`. Soubor v teto slozce je jen podklad, podle
ktereho se to psalo - **menit se musi v databazi a pak publikovat**.

## Snimky obrazovek

Smazany 14. 9. 2026 na pokyn Jirky Honomichla ("k nicemu nejsou dobre").
Byly v nich skutecna jmena zamestnancu, takze do gitu nikdy nesly.
