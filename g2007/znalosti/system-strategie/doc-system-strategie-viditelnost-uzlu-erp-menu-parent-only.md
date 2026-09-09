# Viditelnost uzlu v menu ERP - hodnota parent_only NEznamena "jen rodice" (past, 9.9.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


**Past na jeden radek.** Hodnota `parent_only` u uzlu menu ERP **neznamena "vidi jen rodice"**. Znamena pravy opak - uzel vidi **vsichni**, krome uzivatelu se scoped stromem. Kdo si to vylozi podle nazvu, ohlasi neexistujici problem.

## Jak to je (overeno v kodu)

Rozhoduje funkce `_build_system_root_from_db` v `modules/erp/api/router.py` (kolem r. 58001). Uzel se cloveku zobrazi, pokud plati aspon jedno:

1. **neni scoped** a hodnota je `parent_only` **nebo prazdna (NULL)** -> vidi ho,
2. je vyjmenovan ve `visibility_user_ids` toho uzlu,
3. je **rodic** (`is_marti_parent`) - ten vidi vsechno vcetne `private`.

K tomu se pripocitava **kaskada predku**: kdyz clovek vidi uzel, zviditelni se mu i cesta k nemu.

## Hodnoty, ktere v datech opravdu jsou

Zmereno nad `fw.menu_node` pro `status='active'` dne **9. 9. 2026**:

| hodnota | uzlu | kdo uzel vidi |
|---|---|---|
| `parent_only` | 91 | vsichni krome scoped |
| prazdno (NULL) | 49 | vsichni krome scoped |
| `restricted` | 20 | jen lide ve `visibility_user_ids` (+ rodic) |
| `private` | 16 | jen lide ve `visibility_user_ids` (+ rodic) |

`restricted` a `private` se v podmince chovaji **stejne** - rozdil je jen v pojmenovani.

⚠️ **Hodnota `hr_and_parent` NEEXISTUJE.** Kdyby ji nekdo navrhoval, je to omyl. Stejne tak `tenant_member`, `public` a `parent_or_admin` - ty pochazeji ze **starsiho navrhoveho dokumentu** faze 38.4 nad tabulkou `master.menu_node`, ktera dnes neexistuje (znalost `doc-system-g2007-phase38-4-framework-doctrine` je historicky navrh, ne popis ziveho stavu).

## Scoped uzivatel je jiny mechanismus - ne hodnota

**Scoped NENI hodnota `visibility_scope`.** Je to seznam osob primo v kodu, `_ERP_SCOPED_USERS` v `router.py` (kolem r. 300). Kdo je v nem, ma **osekany strom**: nevidi siroke uzly (`parent_only` ani prazdne) a vidi **jen ty uzly, kde je vyslovne uveden ve `visibility_user_ids`**.

K 9. 9. 2026 je v tom seznamu **jediny clovek - Dusan Havlat (user 41)**, aby v ERP videl jen dochazku sveho tymu.

## Proc to tak vzniklo

- **7. 7. 2026** (Claude-25 se Sarkou): commit `57c94091` predtim zpusobil, ze ne-rodic nevidel v ERP **nic** - 91 ze 114 uzlu je totiz `parent_only`. Opravou se vratilo puvodni chovani, tedy ze `parent_only` a prazdne uzly vidi vsichni. Nazev hodnoty uz se ale nezmenil, a proto klame.
- **8. 7. 2026**: pribyl scoped strom pro Dusana Havlata. (Dve ruzna data, casto se sliji do jednoho.)

## Jak si to overit naostro

Otevri ERP pod uctem, ktery **neni rodic ani scoped**, a podivej se, jestli uzel v strome je. Overeno 9. 9. 2026 pod uctem Jiriho Honomichla (user 20) - uzel `💳 Benefity` (`parent_only`) je v jeho strome videt pod SYSTEM NEW -> 👥 Dochazka.

## Kde je to popsane jeste

Tutez mechaniku popisuje uz znalost **`doc-mzdy-priplatky-srazky`** (oblast mzdy, po rozhodnuti Jirky Honomichla 22. 7. 2026). Je spravna, ale kdo resi viditelnost uzlu, nehleda ji ve znalosti o priplatcich a srazkach - proto tato samostatna znalost.

## Odkud tato znalost vzesla

9. 9. 2026 jsem (Claude-28 s Jirkou) vylozil `parent_only` podle nazvu a ohlasil, ze Sarka Novotna a Petra Safrankova nevidi v ERP uzel Benefity, a tedy ze menu neodpovida kodu. **Nebyla to pravda** - obe ho vidi, rozpor neexistoval. Chyba vznikla tim, ze jsem zaver vyvodil z NAZVU hodnoty, misto abych nasel misto, kde se ta hodnota vyhodnocuje. **Nazev nastaveni neni jeho chovani.**

