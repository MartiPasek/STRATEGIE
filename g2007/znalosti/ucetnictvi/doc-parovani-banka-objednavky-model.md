# Párování banka ↔ objednávky ↔ zakázka — kompletní model (Marti + Claude, 24.6.2026 večer)

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Párování banka ↔ objednávky ↔ zakázka — kompletní model (Marti + Claude, 24.6.2026 večer)

Marti přes „Père Fouras" indicie rozkryl celý párovací model. Tohle je blueprint pro
engine (náhrada Centrálového `EC_Banka_AutoPrirazeniUhradBV`). **Objednávky jsou páteř
na obou stranách — „na nich to všechno stojí."**

## Model — objednávka je střed
| Strana | Faktura | Objednávka (PÁTEŘ) | Platba | Spojka |
|---|---|---|---|---|
| **Nákup** | přijatá faktura FP (řada 500/501) | **vydaná objednávka** (řada 800, druh 6) | my platíme dodavateli | FP.`navazna_objednavka` → vydaná obj. |
| **Prodej** | vydaná faktura FV (řada 600) | **přijatá objednávka** (řada 920+, druh 11) | zákazník platí nám | obj. `CisloZakazky` → zakázka → FV |

## Datový stav (vše v zrcadle `tenant.ec_doklad_zbozi`)
- ✅ **Vydané objednávky** = řada 800 (druh_pohybu **6**), 5 625 ks. FP na ně ukazuje `navazna_objednavka`.
- ✅ **Přijaté objednávky** = řada **920** (+900/910/940/950), druh_pohybu **11**. Řada 920 = 1 155, z toho 1 147 se zakázkou. (= Centrála přehled 506: `DruhPohybuZbo=11 AND RadaDokladu='920'`.)
- ✅ FV vydané faktury = řada 600 (1 735). Vnitroskupina (přefakturace ES↔Control) = řada 601 (cislo_org=0).
- ✅ FP přijaté faktury = řada 500 (7 937).

## Párovací klíče (bankovní transakce → co)
Banka dává nativně: **VS, KS, protiúčet, částka, směr, zpráva** (`bank_transaction_raw`).
1. **Opakované platby** (mzdy/daně/pojištění/FX/poplatky): protiúčet + KS → `bank_predpis` → účet MD/DAL. **Ověřeno: 36/589 sedí** (zdrav 17, daň 12, DPH 4, ČSSZ 3). Strukturální klíč, NE Heliosí text.
2. **Příchozí (zákazník platí naši FV):** VS = jedno z:
   - naše číslo FV (řada 600),
   - vnitroskupina (řada 601),
   - **číslo objednávky zákazníka** (Marti 24.6.),
   - **číslo zakázky zákazníka** (Marti 24.6.).
   → najít v přijatých objednávkách (920) → `CisloZakazky` → zakázka + FV. (`_OznPrjZakaznik` = volný text PO zákazníka, NE čistý VS — proto víc klíčů.)
3. **Odchozí (my platíme dodavateli):** vazba přes **vydanou objednávku** (FP.`navazna_objednavka`). Číslo dodavatelovy faktury v VS na naše číslo nesedne → jde se přes objednávku. (Zpráva často nese naše „501000xxx" = FP.)

## Co postavit (engine — další build)
- **Indexy** na `ec_doklad_zbozi (cislo)`, `(rada, cislo)`, příp. funkční index pro VS match — ad‑hoc korelovaný dotaz přes most TIMEOUTuje (40k×589). Engine musí běžet indexovaně / dávkově.
- **Multi-key matcher**: pro každou transakci zkus klíče v pořadí (opakovaná → naše číslo → objednávka zák. → zakázka zák.) → první shoda vyhrává; nech `bank_zauctovani`/`ucetni_denik` jako dnes (jisté → Marti‑AI podpis, ostatní → návrh).
- **Dotáhnout `_OznPrjZakaznik` + číslo zakázky zákazníka** do zrcadla přijatých objednávek (z Centrály EXT), ať jde matchovat i zákaznické reference.
- **Napojení na `ucetni_denik`** přes zakázku (CisloZakazky) — platba se zaúčtuje a přiřadí na zakázku.

## Stav večer 24.6. — ENGINE LIVE
Model kompletní, data zrcadlená. **Párovací engine postaven a spuštěn** (`/app/bank/parovat`
v `modules/erp/api/bank_api.py` + indexy `ix_ecdz_cislo_norm`/`ix_btr_vs` + `par_*` sloupce).

**První průchod (589 transakcí):** napárováno **93** — opakované 36, FV(600) 26, vnitroskupina(601) 11,
přijaté objednávky(920) 7, ostatní 13. **45 nese zakázku** → řetězec banka→doklad→zakázka stojí.
Příchozí téměř hotové (zbývá 20). **Nenapárováno 496 = z toho 476 ODCHOZÍ** (platby dodavatelům,
VS = jejich číslo faktury → na naše číslo nesedne).

### 🔑 KOLO 10 (HOTOVO) — odchozí přes ZPRÁVU
**Klíč odchozích plateb dodavatelům = `zprava` ve formátu `RRRNNNNNN`** = 3 číslice řada +
číslo NAŠÍ přijaté faktury (platbu generujeme ze systému → do zprávy dáme referenci na FP,
kterou platíme). Příklad: zpráva „500000934" → FP řada 500, číslo 000934 → `navazna_objednavka`
→ zakázka. **Ověřeno 100 %: 251 odchozích, VŠECHNY se zakázkou.** Engine krok C
(`UPDATE … regexp_match(zprava,'^(\d{3})0*(\d+)')`).

**VÝSLEDEK po kole 10: napárováno 344/589 = 58 %, z toho 294 nese zakázku.** Metody:
opakované 36 + VS→doklad 57 + zpráva→FP 251.

**Zbývá 245 (poslední iterace):** odchozí bez kódu ve zprávě / příchozí se zákaznickou
referencí (`_OznPrjZakaznik`, číslo objednávky/zakázky zákazníka). + napojení na `ucetni_denik`
přes zakázku + Fáze 2 platby (`bank_payment_order` → RB `POST /payments/batches` → podpis v IB =
„platit od nás", cíl pondělí).
Hra: kola 8+9+10 zapsána. Engine `/app/bank/parovat` idempotentní (reset+refill), 3 kroky (A/B/C).

— Claude (id=23) + Marti (Père Fouras), 24.6.2026 večer


